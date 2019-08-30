/* -*- Mode:C++; c-file-style:"gnu"; indent-tabs-mode:nil; -*- */
/*
 * Copyright 2007 University of Washington
 * 
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License version 2 as
 * published by the Free Software Foundation;
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
 *
 * Author:  Tom Henderson (tomhend@u.washington.edu)
 */
#include "ns3/address.h"
#include "ns3/address-utils.h"
#include "ns3/log.h"
#include "ns3/inet-socket-address.h"
#include "ns3/inet6-socket-address.h"
#include "ns3/node.h"
#include "ns3/socket.h"
#include "ns3/udp-socket.h"
#include "ns3/simulator.h"
#include "ns3/socket-factory.h"
#include "ns3/packet.h"
#include "ns3/trace-source-accessor.h"
#include "ns3/udp-socket-factory.h"
#include "server.h"
#include "qos-header.h"

namespace ns3 {

NS_LOG_COMPONENT_DEFINE ("Server");

NS_OBJECT_ENSURE_REGISTERED (Server);

TypeId 
Server::GetTypeId (void)
{
  static TypeId tid = TypeId ("ns3::Server")
    .SetParent<Application> ()
    .SetGroupName("nrel-app")
    .AddConstructor<Server> ()
    .AddAttribute ("Local",
                   "The Address on which to Bind the rx socket.",
                   AddressValue (),
                   MakeAddressAccessor (&Server::m_local),
                   MakeAddressChecker ())
    .AddAttribute ("Protocol",
                   "The type id of the protocol to use for the rx socket.",
                   TypeIdValue (UdpSocketFactory::GetTypeId ()),
                   MakeTypeIdAccessor (&Server::m_tid),
                   MakeTypeIdChecker ())
    .AddTraceSource ("feedback",
                    "QOE feedback",
                    MakeTraceSourceAccessor (&Server::m_feedback),
                    "ns3::TracedValueCallback::Int32")
    .AddTraceSource ("Rx",
                     "A packet has been received",
                     MakeTraceSourceAccessor (&Server::m_rxTrace),
                     "ns3::Packet::AddressTracedCallback")
  ;
  return tid;
}

Server::Server ()
{
  NS_LOG_FUNCTION (this);
  m_socket = 0;
  m_totalRx = 0;
  m_received = 0;
  m_latency = 0;
  m_throughput = 0;
  m_Maxlatency = 0;
  m_Minthroughput = 60000;
  m_initTx = 0;
  m_id = 0;
}

Server::~Server()
{
  NS_LOG_FUNCTION (this);
}

uint32_t Server::GetTotalRx () const
{
  NS_LOG_FUNCTION (this);
  return m_totalRx;
}

Ptr<Socket>
Server::GetListeningSocket (void) const
{
  NS_LOG_FUNCTION (this);
  return m_socket;
}

std::list<Ptr<Socket> >
Server::GetAcceptedSockets (void) const
{
  NS_LOG_FUNCTION (this);
  return m_socketList;
}

void Server::DoDispose (void)
{
  NS_LOG_FUNCTION (this);
  m_socket = 0;
  m_socketList.clear ();

  // chain up
  Application::DoDispose ();
}


// Application Methods
void Server::StartApplication ()    // Called at time specified by Start
{
  // NS_LOG_INFO ("Server starts");
  NS_LOG_FUNCTION (this);
  // Create the socket if not already
  if (!m_socket)
    {
      m_socket = Socket::CreateSocket (GetNode (), m_tid);
      m_socket->Bind (m_local);
      m_socket->Listen ();
      m_socket->ShutdownSend ();
      if (addressUtils::IsMulticast (m_local))
        {
          Ptr<UdpSocket> udpSocket = DynamicCast<UdpSocket> (m_socket);
          if (udpSocket)
            {
              // equivalent to setsockopt (MCAST_JOIN_GROUP)
              udpSocket->MulticastJoinGroup (0, m_local);
            }
          else
            {
              NS_FATAL_ERROR ("Error: joining multicast on a non-UDP socket");
            }
        }
    }

  m_socket->SetRecvCallback (MakeCallback (&Server::HandleRead, this));
  m_socket->SetAcceptCallback (
    MakeNullCallback<bool, Ptr<Socket>, const Address &> (),
    MakeCallback (&Server::HandleAccept, this));
  m_socket->SetCloseCallbacks (
    MakeCallback (&Server::HandlePeerClose, this),
    MakeCallback (&Server::HandlePeerError, this));
}

void Server::StopApplication ()     // Called at time specified by Stop
{
  NS_LOG_FUNCTION (this); 
  std::cout << "At time " << Simulator::Now ().GetSeconds ()<< "s Server received "<<  m_totalRx << " bytes across "<<m_received<<" packets, from Client "<<m_id<<", Average Latency: " << m_latency << "ms, Average Throughput: "<<m_throughput<<"kbps, Max Latency: "<<m_Maxlatency<<"ms, Min Throughput: "<<m_Minthroughput<<"kbps\n";

  while(!m_socketList.empty ()) //these are accepted sockets, close them
    {
      Ptr<Socket> acceptedSocket = m_socketList.front ();
      m_socketList.pop_front ();
      acceptedSocket->Close ();
      NS_LOG_INFO("Closed Socket: "<<acceptedSocket);
    }
  if (m_socket) 
    {
      m_socket->Close ();
      m_socket->SetRecvCallback (MakeNullCallback<void, Ptr<Socket> > ());
    }
  NS_LOG_INFO ("Server is closed");
}

void Server::HandleRead (Ptr<Socket> socket)
{
  NS_LOG_FUNCTION (this << socket);
  Ptr<Packet> packet;
  Address from;
  while ((packet = socket->RecvFrom (from)))
    {
      if (packet->GetSize () == 0)
        { //EOF
          break;
        }
      
      QosHeader QosTx;
      NS_LOG_INFO ("Packet Of Serialized Size: " << packet->GetSerializedSize());
      packet->RemoveHeader (QosTx);
      if(QosTx.GetID()){
        if(m_received == 0){
          if(QosTx.GetTs().GetMilliSeconds()>0)
            m_initTx = QosTx.GetTs().GetMilliSeconds();
          else
            continue;
          m_id = QosTx.GetID();
        }
        
        double delay=Simulator::Now().GetMilliSeconds() - QosTx.GetTs().GetMilliSeconds();
	
        if(delay>0){
          if(m_Maxlatency<=delay)
            m_Maxlatency = delay;
          m_totalRx += (packet->GetSize()+20);
          m_latency = (m_latency*m_received + delay)/(m_received+1);
          m_received++;
          m_throughput = m_totalRx*8/(QosTx.GetNextTs().GetMilliSeconds() - m_initTx);
          double datarate=(packet->GetSize()+20)*8/(QosTx.GetNextTs().GetMilliSeconds() - QosTx.GetTs().GetMilliSeconds());
          if(datarate<=m_Minthroughput)
             m_Minthroughput = datarate;
        }
        else
          continue;
      }
       /* if (m_id==265)
        {        
                NS_LOG_UNCOND("At time " << Simulator::Now ().GetSeconds ()<< "s Server received "<<  m_totalRx << " bytes from Client "<<m_id<<" Total packets="<<m_received<<" MEasured Throughput: "<<m_throughput);
                
        }*/
      NS_LOG_INFO ("At time " << Simulator::Now ().GetSeconds ()<< "s Server received "<<  m_totalRx << " bytes from Client "<<m_id);
      m_rxTrace (packet, from);
    }
}


void Server::HandlePeerClose (Ptr<Socket> socket)
{
  NS_LOG_FUNCTION (this << socket);
}
 
void Server::HandlePeerError (Ptr<Socket> socket)
{
  NS_LOG_FUNCTION (this << socket);
}
 

void Server::HandleAccept (Ptr<Socket> s, const Address& from)
{
  NS_LOG_FUNCTION (this << s << from);
  s->SetRecvCallback (MakeCallback (&Server::HandleRead, this));
  m_socketList.push_back (s);
}

} // Namespace ns3


#include "ns3/log.h"
#include "ns3/address.h"
#include "ns3/inet-socket-address.h"
#include "ns3/inet6-socket-address.h"
#include "ns3/packet-socket-address.h"
#include "ns3/node.h"
#include "ns3/nstime.h"
#include "ns3/data-rate.h"
#include "ns3/socket.h"
#include "ns3/simulator.h"
#include "ns3/socket-factory.h"
#include "ns3/packet.h"
#include "ns3/uinteger.h"
#include "ns3/trace-source-accessor.h"
#include "client.h"
#include "qos-header.h"
#include "ns3/udp-socket-factory.h"
#include "ns3/string.h"
#include "ns3/pointer.h"

namespace ns3 {

NS_LOG_COMPONENT_DEFINE ("Client");

NS_OBJECT_ENSURE_REGISTERED (Client);

TypeId
Client::GetTypeId (void)
{
  static TypeId tid = TypeId ("ns3::Client")
    .SetParent<Application> ()
    .SetGroupName("nrel-app")
    .AddConstructor<Client> ()
    .AddAttribute ("DataRate", "The data rate in on state.",
                   DataRateValue (DataRate ("500kb/s")),
                   MakeDataRateAccessor (&Client::m_cbrRate),
                   MakeDataRateChecker ())
    .AddAttribute ("PacketSize", "The size of packets sent in on state",
                   UintegerValue (512),
                   MakeUintegerAccessor (&Client::m_pktSize),
                   MakeUintegerChecker<uint32_t> (1))
    .AddAttribute ("Remote", "The address of the destination",
                   AddressValue (),
                   MakeAddressAccessor (&Client::m_peer),
                   MakeAddressChecker ())
    .AddAttribute ("ClientID", "The ID of the client application",
                   UintegerValue (0),
                   MakeUintegerAccessor (&Client::m_id),
                   MakeUintegerChecker<uint32_t> (0))
    .AddAttribute ("MaxBytes", 
                   "The total number of bytes to send. Once these bytes are sent, "
                   "no packet is sent again, even in on state. The value zero means "
                   "that there is no limit.",
                   UintegerValue (0),
                   MakeUintegerAccessor (&Client::m_maxBytes),
                   MakeUintegerChecker<uint32_t> ())
    .AddAttribute ("Protocol", "The type of protocol to use.",
                   TypeIdValue (UdpSocketFactory::GetTypeId ()),
                   MakeTypeIdAccessor (&Client::m_tid),
                   MakeTypeIdChecker ())
    .AddTraceSource ("Tx", "A new packet is created and is sent",
                     MakeTraceSourceAccessor (&Client::m_txTrace),
                     "ns3::Packet::TracedCallback")
  ;
  return tid;
}


Client::Client ()
  : m_socket (0),
    m_connected (false),
    m_residualBits (0),
    m_lastStartTime (Seconds (0)),
    m_totBytes (0),
    m_id (0),
    m_timeMult (0)
{
  NS_LOG_FUNCTION (this);
}

Client::~Client()
{
  NS_LOG_FUNCTION (this);
}

void 
Client::SetMaxBytes (uint32_t maxBytes)
{
  NS_LOG_FUNCTION (this << maxBytes);
  m_maxBytes = maxBytes;
}

Ptr<Socket>
Client::GetSocket (void) const
{
  NS_LOG_FUNCTION (this);
  return m_socket;
}

void
Client::DoDispose (void)
{
  NS_LOG_FUNCTION (this);

  m_socket = 0;
  // chain up
  Application::DoDispose ();
}

// Application Methods
void Client::StartApplication () // Called at time specified by Start
{
  NS_LOG_FUNCTION (this);
  // NS_LOG_INFO ("Client starts");
  // Create the socket if not already
  if (!m_socket)
    {
      m_socket = Socket::CreateSocket (GetNode (), m_tid);
      if (Inet6SocketAddress::IsMatchingType (m_peer))
        {
          m_socket->Bind6 ();
        }
      else if (InetSocketAddress::IsMatchingType (m_peer) ||
               PacketSocketAddress::IsMatchingType (m_peer))
        {
          m_socket->Bind ();
        }
      m_socket->Connect (m_peer);
      m_socket->SetAllowBroadcast (true);
      m_socket->ShutdownRecv ();

      m_socket->SetConnectCallback (
        MakeCallback (&Client::ConnectionSucceeded, this),
        MakeCallback (&Client::ConnectionFailed, this));
    }
  m_cbrRateFailSafe = m_cbrRate;
  uint8_t timeResolution=(Simulator::Now ().GetResolution()-4);
  m_timeMult=1;
  while(timeResolution>0)
  {
  	m_timeMult=m_timeMult*1000;
	timeResolution=timeResolution-1;
  }
  StartSending ();
}

void Client::StopApplication () // Called at time specified by Stop
{
  NS_LOG_FUNCTION (this);
  std::cout << "At time " << Simulator::Now ().GetSeconds ()<< "s Client "<<m_id<<" Sent "<<  m_totBytes/m_pktSize << " Packets of total size "<<m_totBytes<<" bytes\n";
  CancelEvents ();
  if(m_socket != 0)
    {
      m_socket->Close ();
      m_connected = false;
    }
  else
    {
      NS_LOG_WARN ("Client found null socket to close in StopApplication");
    }
  // NS_LOG_INFO ("Client is closed");
}


void Client::CancelEvents ()
{
  NS_LOG_FUNCTION (this);

  if (m_sendEvent.IsRunning () && m_cbrRateFailSafe == m_cbrRate )
    { // Cancel the pending send packet event
      // Calculate residual bits since last packet sent
      Time delta (Simulator::Now () - m_lastStartTime);
      int64x64_t bits = delta.To (Time::S) * m_cbrRate.GetBitRate ();
      m_residualBits += bits.GetHigh ();
    }
  m_cbrRateFailSafe = m_cbrRate;
  Simulator::Cancel (m_sendEvent);
}


// Event handlers
void Client::StartSending ()
{
  NS_LOG_FUNCTION (this);
  m_lastStartTime = Simulator::Now ();
  ScheduleNextTx ();  // Schedule the send packet event
}


// Private helpers
void Client::ScheduleNextTx ()
{
  NS_LOG_FUNCTION (this);

  if (m_maxBytes == 0 || m_totBytes < m_maxBytes)
    {
      uint32_t bits = m_pktSize * 8 - m_residualBits;
      NS_LOG_LOGIC ("bits = " << bits);
      Time nextTime (Seconds (bits /
                              static_cast<double>(m_cbrRate.GetBitRate ()))); // Time till next packet
      NS_LOG_LOGIC ("nextTime = " << nextTime);
      m_sendEvent = Simulator::Schedule (nextTime,
                                         &Client::SendPacket, this);
    }
  else
    { // All done, cancel any pending events
      StopApplication ();
    }
}

void Client::SendPacket ()
{
  NS_LOG_FUNCTION (this);
  
  NS_ASSERT (m_sendEvent.IsExpired ());
  QosHeader QosTx;
  QosTx.SetID(m_id);
  QosTx.SetTs(Simulator::Now ().GetTimeStep ());
  
  QosTx.SetNextTs(uint64_t(Simulator::Now ().GetTimeStep()) + double(m_pktSize*m_timeMult*8/ m_cbrRate.GetBitRate())); // Time till next packet
  Ptr<Packet> packet = Create<Packet> (m_pktSize-(8+8+4)); // 8+8+4 : the size of the QoS header
  packet->AddHeader (QosTx);
	/*if (m_id==265)
        {   
  		NS_LOG_UNCOND ("At time " << Simulator::Now ().GetSeconds ()<< "s client "<<m_id<<" sent "<< packet<<" with timestamp: "<<QosTx.GetTs().GetMilliSeconds()<<" with Nexttime: "<<QosTx.GetNextTs().GetMilliSeconds());
	}*/
  m_txTrace (packet);
  m_socket->Send (packet);
  m_totBytes += m_pktSize;
   if (InetSocketAddress::IsMatchingType (m_peer))
     {
       NS_LOG_INFO ("At time " << Simulator::Now ().GetSeconds ()
                    << "s client "<<m_id<<" sent "
                    <<  packet->GetSize () << " bytes to "
                    << InetSocketAddress::ConvertFrom(m_peer).GetIpv4 ()
                    << " port " << InetSocketAddress::ConvertFrom (m_peer).GetPort ()
                    << " total Tx " << m_totBytes << " bytes");
     }
   else if (Inet6SocketAddress::IsMatchingType (m_peer))
     {
       NS_LOG_INFO ("At time " << Simulator::Now ().GetSeconds ()
                    << "s client "<<m_id<<" sent "
                    <<  packet->GetSize () << " bytes to "
                    << Inet6SocketAddress::ConvertFrom(m_peer).GetIpv6 ()
                    << " port " << Inet6SocketAddress::ConvertFrom (m_peer).GetPort ()
                    << " total Tx " << m_totBytes << " bytes");
     }
  m_lastStartTime = Simulator::Now ();
  m_residualBits = 0;
  ScheduleNextTx ();
}


void Client::ConnectionSucceeded (Ptr<Socket> socket)
{
  NS_LOG_FUNCTION (this << socket);
  m_connected = true;
}

void Client::ConnectionFailed (Ptr<Socket> socket)
{
  NS_LOG_FUNCTION (this << socket);
}


} // Namespace ns3

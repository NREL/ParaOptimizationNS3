

#ifndef NETROUTER_H
#define NETROUTER_H

#include "ns3/application.h"
#include "ns3/event-id.h"
#include "ns3/ptr.h"
#include "ns3/traced-callback.h"
#include "ns3/traced-value.h"
#include "ns3/address.h"

namespace ns3 {

class Address;
class Socket;
class Packet;

class NetRouter : public Application 
{
public:

  static TypeId GetTypeId (void);
  NetRouter ();

  virtual ~NetRouter ();

  uint32_t GetTotalRx () const;

  Ptr<Socket> GetSocketIn (void) const;

  Ptr<Socket> GetSocketOut (void) const;

  std::list<Ptr<Socket> > GetAcceptedSockets (void) const;
 
protected:
  virtual void DoDispose (void);
private:
  // inherited from Application base class.
  virtual void StartApplication (void);    // Called at time specified by Start
  virtual void StopApplication (void);     // Called at time specified by Stop

  void HandleRead (Ptr<Socket> socket);
 
  void HandleAccept (Ptr<Socket> socket, const Address& from);

  void HandlePeerClose (Ptr<Socket> socket);
 
  void HandlePeerError (Ptr<Socket> socket);

  void ConnectionSucceeded (Ptr<Socket> socket);

  void ConnectionFailed (Ptr<Socket> socket);

  void SendData ();


  Ptr<Socket>               m_socketin;           //!< Listening socket
  Ptr<Socket>               m_socketout;          //!<  socket
  std::list<Ptr<Socket> >   m_socketList;         //!< the accepted sockets
  Ptr<Packet>               m_packet;             //!< forwarded packet
  Address                   m_localin;            //!< Local in address to bind to
  Address                   m_remoteout;          //!< Address of the destination
  TypeId                    m_tidin;              //!< Protocol In TypeId
  TypeId                    m_tidout;             //!< Protocol Out TypeId
  uint64_t		    m_last_Rx_time[500];  // Fix to ignore duplicate packets
  bool                      m_connected;          //!< True if connected
  uint32_t                  m_id;                 //!< ID of the NetRouter application 

};

} // namespace ns3

#endif /* NETROUTER_H */


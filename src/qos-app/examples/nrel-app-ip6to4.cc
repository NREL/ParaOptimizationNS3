
// Network topology
//
//      n0                                      n1
//  +---------+    +---------+--------+     +--------+
//  | UDP     |    |     NetRouter    |     | UDP    |
//  +---------+    +---------+--------+     +--------+
//  | IPv6    |    | IPv6    | IPv4   |     | IPv4   |
//  +---------+    +---------+--------+     +--------+
//  | 6LoWPAN |    | 6LoWPAN |        |     |        |
//  +---------+    +---------+  WIFI  +     +  WIFI  +
//  | LoWPAN  |    | LoWPAN  |  Mesh  |     |  Mesh  |
//  +---------+    +---------+--------+     +--------+
//       |              |        |               |
//       ================        =================
//  Traffic Direction: n0 ---------> n1


#include <fstream>
#include "ns3/core-module.h"
#include "ns3/internet-module.h"
#include "ns3/csma-module.h"
#include "ns3/internet-apps-module.h"
#include "ns3/ipv6-static-routing-helper.h"
#include "ns3/ipv6-routing-table-entry.h"
#include "ns3/sixlowpan-module.h"
#include "ns3/lr-wpan-module.h"
#include "ns3/wifi-module.h"
#include "ns3/mesh-module.h"
#include "ns3/mobility-module.h"
#include "ns3/mesh-helper.h"
#include "ns3/network-module.h"
#include "ns3/nrel-app-module.h"


using namespace ns3;

NS_LOG_COMPONENT_DEFINE ("NrelAppIP6to4");

int main (int argc, char** argv)
{
  bool verbose          = true;
  uint16_t udp          = 1;
  uint64_t datarate     = 24000;
  double simulationTime = 10;
  double distance       = 50;
  Time::SetResolution (Time::NS);

  CommandLine cmd;
  cmd.AddValue ("verbose", "turn on some relevant log components", verbose);
  cmd.AddValue ("udp", "UDP if set to 1, TCP otherwise", udp);
  cmd.AddValue ("datarate", "DataRate of application (bps)", datarate);
  cmd.AddValue ("simulationTime", "Simulation time in seconds", simulationTime);
  cmd.AddValue ("distance", "Distance in meters between the station and the access point", distance);
  cmd.Parse (argc, argv);

  if (verbose)
    {
      LogComponentEnable ("NrelAppIP6to4", LOG_LEVEL_INFO);
      LogComponentEnable ("Server", LOG_LEVEL_INFO);
      // LogComponentEnable ("Client", LOG_LEVEL_INFO);
      // LogComponentEnable ("NetRouter", LOG_LEVEL_INFO); 
      // LogComponentEnable ("Socket", LOG_LEVEL_ALL);
    }

  NS_LOG_INFO ("Create nodes.");
  Ptr<Node> n0 = CreateObject<Node> ();
  Ptr<Node> r = CreateObject<Node> ();
  Ptr<Node> n1 = CreateObject<Node> ();


  NodeContainer net1 (n0, r);
  NodeContainer net2 (r, n1);
  NodeContainer all (n0, r, n1);

  MobilityHelper mobility;
  mobility.SetPositionAllocator ("ns3::GridPositionAllocator",
                                 "MinX", DoubleValue (0.0),
                                 "MinY", DoubleValue (0.0),
                                 "DeltaX", DoubleValue (distance),
                                 "DeltaY", DoubleValue (distance),
                                 "GridWidth", UintegerValue (10),
                                 "LayoutType", StringValue ("RowFirst"));
  mobility.SetMobilityModel ("ns3::ConstantPositionMobilityModel");
  mobility.Install (all);

  NS_LOG_INFO ("Create IPv6 Internet Stack");
  InternetStackHelper internet;
  internet.Install (all);

  NS_LOG_INFO ("Create channels.");

  LrWpanHelper lrWpanHelper;
  NetDeviceContainer lrwpanDevices = lrWpanHelper.Install(net1);
  lrWpanHelper.AssociateToPan (lrwpanDevices, 0);

  SixLowPanHelper sixlowpan;
  NetDeviceContainer d1 = sixlowpan.Install (lrwpanDevices); 


  YansWifiPhyHelper wifiPhy = YansWifiPhyHelper::Default ();
  YansWifiChannelHelper wifiChannel = YansWifiChannelHelper::Default ();
  wifiPhy.SetChannel (wifiChannel.Create ());

  MeshHelper mesh;
  mesh = MeshHelper::Default ();
  mesh.SetStackInstaller ("ns3::Dot11sStack");
  mesh.SetSpreadInterfaceChannels (MeshHelper::SPREAD_CHANNELS);
  mesh.SetMacType ("RandomStart", TimeValue (Seconds (0.1)));
  mesh.SetNumberOfInterfaces (1);

  NetDeviceContainer d2 = mesh.Install (wifiPhy, net2);

  NS_LOG_INFO ("Create networks and assign IPv6&IPv4 Addresses.");
  Ipv6AddressHelper ipv6;
  ipv6.SetBase (Ipv6Address ("2001:1::"), Ipv6Prefix (64));
  Ipv6InterfaceContainer i1 = ipv6.Assign (d1);
  i1.SetForwarding (1, true);
  i1.SetDefaultRouteInAllNodes (1);
  
  Ipv4AddressHelper ipv4;
  ipv4.SetBase ("10.1.1.0", "255.255.255.0");
  Ipv4InterfaceContainer i2 = ipv4.Assign (d2);

  NS_LOG_INFO ("Create application and transmit data from n0 to n1");
  
  if(udp){
    NS_LOG_INFO ("Create UDP connnection and transmit data from n0 to n1");
    uint16_t port1 = 80;
    uint16_t port2 = 8080;
    Address LocalAddress (InetSocketAddress (Ipv4Address::GetAny (), port2));
    ServerHelper serverAppHelper ("ns3::UdpSocketFactory", LocalAddress);

    ApplicationContainer serverApp;
    serverApp = serverAppHelper.Install (n1);
    serverApp.Start (Seconds (1.0));
    serverApp.Stop (Seconds (simulationTime+3));

    Address RemoteAddress (Inet6SocketAddress (i1.GetAddress (1, 1), port1));
    ClientHelper clientAppHelper ("ns3::UdpSocketFactory",RemoteAddress);
    clientAppHelper.SetAttribute ("ClientID", UintegerValue (251));
    clientAppHelper.SetAttribute ("PacketSize", UintegerValue (300));
    clientAppHelper.SetAttribute ("DataRate", DataRateValue (datarate)); //bit/s
    NS_LOG_INFO ("Application Sending Rate : "<< datarate/1000.0 << "kbps");

    ApplicationContainer clientApp;
    clientApp.Add (clientAppHelper.Install (n0));
    clientApp.Start (Seconds (2));
    clientApp.Stop (Seconds (simulationTime+2));

    Address localIn (Inet6SocketAddress (Ipv6Address::GetAny (), port1));
    Address remoteOut (InetSocketAddress (i2.GetAddress (1), port2));
    NetRouterHelper netRouterHelper("ns3::UdpSocketFactory", localIn, "ns3::UdpSocketFactory", remoteOut);
    ApplicationContainer netrouterApp;
    netrouterApp.Add (netRouterHelper.Install (r));
    netrouterApp.Start (Seconds (1.0));
    netrouterApp.Stop (Seconds (simulationTime+3));
  }
  else{
    NS_LOG_INFO ("Create TCP connnection and transmit data from n0 to n1");
    uint16_t port1 = 80;
    uint16_t port2 = 8080;
    Address LocalAddress (InetSocketAddress (Ipv4Address::GetAny (), port2));
    ServerHelper serverAppHelper ("ns3::TcpSocketFactory", LocalAddress);

    ApplicationContainer serverApp;
    serverApp = serverAppHelper.Install (n1);
    serverApp.Start (Seconds (1.0));
    serverApp.Stop (Seconds (simulationTime+3));
    
    Address RemoteAddress (Inet6SocketAddress (i1.GetAddress (1, 1), port1));
    ClientHelper clientAppHelper ("ns3::TcpSocketFactory",RemoteAddress);
    clientAppHelper.SetAttribute ("ClientID", UintegerValue (251));
    clientAppHelper.SetAttribute ("PacketSize", UintegerValue (300));
    clientAppHelper.SetAttribute ("DataRate", DataRateValue (datarate)); //bit/s
    NS_LOG_INFO ("Application Sending Rate : "<< datarate/1000.0 << "kbps");

    ApplicationContainer clientApp;
    clientApp.Add (clientAppHelper.Install (n0));
    clientApp.Start (Seconds (2));
    clientApp.Stop (Seconds (simulationTime+2));

    Address localIn (Inet6SocketAddress (Ipv6Address::GetAny (), port1));
    Address remoteOut (InetSocketAddress (i2.GetAddress (1), port2));
    NetRouterHelper netRouterHelper("ns3::TcpSocketFactory", localIn, "ns3::TcpSocketFactory", remoteOut);
    ApplicationContainer netrouterApp;
    netrouterApp.Add (netRouterHelper.Install (r));
    netrouterApp.Start (Seconds (1.0));
    netrouterApp.Stop (Seconds (simulationTime+3));
  }


  NS_LOG_INFO ("Run Simulation.");
  Simulator::Stop (Seconds (simulationTime+4));
  Simulator::Run ();
  Simulator::Destroy ();
  NS_LOG_INFO ("Done.");
  return 0;
}


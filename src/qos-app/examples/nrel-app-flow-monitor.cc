
#include "ns3/core-module.h"
#include "ns3/network-module.h"
#include "ns3/internet-module.h"
#include "ns3/point-to-point-module.h"
#include "ns3/point-to-point-helper.h"
#include "ns3/nrel-app-module.h"

using namespace ns3;

NS_LOG_COMPONENT_DEFINE ("NrelAppFlowMonitor");

int
main (int argc, char *argv[])
{
  Time::SetResolution (Time::NS);
  LogComponentEnable ("Server", LOG_LEVEL_INFO);

  NodeContainer nodes;
  nodes.Create (2);

  PointToPointHelper pointToPoint;
  pointToPoint.SetDeviceAttribute ("DataRate", StringValue ("1Mbps"));
  pointToPoint.SetChannelAttribute ("Delay", StringValue ("2ms"));

  NetDeviceContainer devices;
  devices = pointToPoint.Install (nodes);

  InternetStackHelper stack;
  stack.Install (nodes);

  Ipv4AddressHelper address;
  address.SetBase ("10.1.1.0", "255.255.255.0");

  Ipv4InterfaceContainer interfaces = address.Assign (devices);


  uint16_t port = 8080;
  Address apLocalAddress (InetSocketAddress (Ipv4Address::GetAny (), port));
  ServerHelper serverAppHelper ("ns3::UdpSocketFactory", apLocalAddress);

  ApplicationContainer serverApp;
  serverApp = serverAppHelper.Install (nodes.Get (1));
  serverApp.Start (Seconds (0.0));
  serverApp.Stop (Seconds (12));

  Address remoteAddress (InetSocketAddress (interfaces.GetAddress (1), port));
  ClientHelper clientAppHelper ("ns3::UdpSocketFactory",remoteAddress);
  clientAppHelper.SetAttribute ("ClientID", UintegerValue (251));
  clientAppHelper.SetAttribute ("PacketSize", UintegerValue (300));
  clientAppHelper.SetAttribute ("DataRate", DataRateValue (240000)); //bit/s

  ApplicationContainer clientApp;
  clientApp.Add (clientAppHelper.Install (nodes.Get (0)));
  clientApp.Start (Seconds (1));
  clientApp.Stop (Seconds (11));

  Simulator::Stop (Seconds (13));
  Simulator::Run ();
  Simulator::Destroy ();
  return 0;
}

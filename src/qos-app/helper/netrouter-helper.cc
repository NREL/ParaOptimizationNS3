
#include "netrouter-helper.h"
#include "ns3/string.h"
#include "ns3/inet-socket-address.h"
#include "ns3/packet-socket-address.h"
#include "ns3/names.h"

namespace ns3 {

NetRouterHelper::NetRouterHelper (std::string protocolIn, Address localIn, std::string protocolOut, Address remoteOut)
{
  m_factory.SetTypeId ("ns3::NetRouter");
  m_factory.Set ("ProtocolIn", StringValue (protocolIn));
  m_factory.Set ("LocalIn", AddressValue (localIn));
  m_factory.Set ("ProtocolOut", StringValue (protocolOut));
  m_factory.Set ("RemoteOut", AddressValue (remoteOut));
}

void 
NetRouterHelper::SetAttribute (std::string name, const AttributeValue &value)
{
  m_factory.Set (name, value);
}

ApplicationContainer
NetRouterHelper::Install (Ptr<Node> node) const
{
  return ApplicationContainer (InstallPriv (node));
}

ApplicationContainer
NetRouterHelper::Install (std::string nodeName) const
{
  Ptr<Node> node = Names::Find<Node> (nodeName);
  return ApplicationContainer (InstallPriv (node));
}

ApplicationContainer
NetRouterHelper::Install (NodeContainer c) const
{
  ApplicationContainer apps;
  for (NodeContainer::Iterator i = c.Begin (); i != c.End (); ++i)
    {
      apps.Add (InstallPriv (*i));
    }

  return apps;
}

Ptr<Application>
NetRouterHelper::InstallPriv (Ptr<Node> node) const
{
  Ptr<Application> app = m_factory.Create<Application> ();
  node->AddApplication (app);

  return app;
}

}

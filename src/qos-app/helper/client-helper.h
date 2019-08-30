
#ifndef CLIENT_HELPER_H
#define CLIENT_HELPER_H

#include <stdint.h>
#include <string>
#include "ns3/object-factory.h"
#include "ns3/address.h"
#include "ns3/attribute.h"
#include "ns3/net-device.h"
#include "ns3/node-container.h"
#include "ns3/application-container.h"
// #include "ns3/client.h"

namespace ns3 {

class DataRate;


class ClientHelper
{
public:

  ClientHelper (std::string protocol, Address address);

  void SetAttribute (std::string name, const AttributeValue &value);

  void SetConstantRate (DataRate dataRate, uint32_t packetSize = 512);

  ApplicationContainer Install (NodeContainer c) const;

  ApplicationContainer Install (Ptr<Node> node) const;

  ApplicationContainer Install (std::string nodeName) const;

private:

  Ptr<Application> InstallPriv (Ptr<Node> node) const;

  ObjectFactory m_factory; //!< Object factory.
};

} // namespace ns3

#endif /* CLIENT_HELPER_H */


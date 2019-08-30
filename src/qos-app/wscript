# -*- Mode: python; py-indent-offset: 4; indent-tabs-mode: nil; coding: utf-8; -*-

# def options(opt):
#     pass

# def configure(conf):
#     conf.check_nonfatal(header_name='stdint.h', define_name='HAVE_STDINT_H')

def build(bld):
    module = bld.create_ns3_module('nrel-app', ['internet','stats'])
    module.source = [
        'model/client.cc',
        'model/server.cc',
        'model/qos-header.cc',
        'model/netrouter.cc',
        'helper/client-helper.cc',
        'helper/server-helper.cc',
        'helper/netrouter-helper.cc',
        ]

    module_test = bld.create_ns3_module_test_library('nrel-app')
    module_test.source = [
        'test/nrel-app-test-suite.cc',
        ]

    headers = bld(features='ns3header')
    headers.module = 'nrel-app'
    headers.source = [
        'model/client.h',
        'model/server.h',
        'model/qos-header.h',
        'model/netrouter.h',
        'helper/client-helper.h',
        'helper/server-helper.h',
        'helper/netrouter-helper.h',
        ]

    if bld.env.ENABLE_EXAMPLES:
        bld.recurse('examples')

    # bld.ns3_python_bindings()


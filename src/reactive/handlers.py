#!/bin/bash
# Copyright 2016 AT&T Intellectual Property, Inc. All Rights Reserved.
#  
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#  
# http://www.apache.org/licenses/LICENSE-2.0
#  
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# What this is: Support script defining hooks used during installation of 
# OpenStack Congress via JuJu.

import charms.reactive as reactive
import charmhelpers.core.hookenv as hookenv

# This charm's library contains all of the handler code associated with
# congress
import charm.openstack.congress as congress


# use a synthetic state to ensure that it get it to be installed independent of
# the install hook.
@reactive.when_not('charm.installed')
def install_packages():
    congress.install()
    reactive.set_state('charm.installed')


@reactive.when('amqp.connected')
def setup_amqp_req(amqp):
    """Use the amqp interface to request access to the amqp broker using our
    local configuration.
    """
    amqp.request_access(username='congress',
                        vhost='openstack')


@reactive.when('shared-db.connected')
def setup_database(database):
    """On receiving database credentials, configure the database on the
    interface.
    """
    database.configure('congress', 'congress', hookenv.unit_private_ip())


@reactive.when('identity-service.connected')
def setup_endpoint(keystone):
    congress.setup_endpoint(keystone)


@reactive.when('shared-db.available')
@reactive.when('identity-service.available')
@reactive.when('amqp.available')
def render_stuff(*args):
    congress.render_configs(args)
    reactive.set_state('config.complete')

@reactive.when('config.complete')
@reactive.when_not('db.synched')
def run_db_migration():
    congress.db_sync()
    congress.restart_all()
    reactive.set_state('db.synched')

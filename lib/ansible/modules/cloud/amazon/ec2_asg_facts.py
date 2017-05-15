#!/usr/bin/python
# -*- coding: utf-8 -*-
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

DOCUMENTATION = '''
---
module: ec2_asg_facts
author: "Stefan Horning (@stefanhorning)"
version_added: "2.2"
short_description: Gather facts about EC2 auto scaling groups in AWS
description:
    - Finds a list of existing EC2 auto scaling groups based on given filters. This module has a dependency on python-boto >= 2.5
options:
  names:
    description:
      - List of all auto scaling group names to gather facts about. Pass this option to gather facts about a set of ASGs, otherwise, all ASGs are returned.
    required: false
    default: null
  health_check_type:
    description:
      - type of the autoscaling groups health check, can be EC2 or ELB.
    required: false
extends_documentation_fragment:
    - aws
    - ec2
'''

EXAMPLES = '''
# Gather facts about all ASGs
- action:
    module: ec2_asg_facts
  register: asg_facts

- action:
    module: debug
    msg: "{{ item.name }}"
  with_items: asg_facts.asgs

# Gather facts about a particular ASG
- action:
    module: ec2_asg_facts
    names: app-servers
  register: asg_facts

- action:
    module: debug
    msg: "{{ asg_facts.asgs.0.dns_name }}"

# Gather facts about a set of ASGs
- action:
    module: ec2_asg_facts
    names:
    - frontend-prod
    - backend-prod
  register: asg_facts

- action:
    module: debug
    msg: "{{ item.name }}"
  with_items: asg_facts.asgs
'''

try:
    import boto.ec2
    from boto.ec2.autoscale import AutoScaleConnection, AutoScalingGroup, Tag
    from boto.exception import BotoServerError
    HAS_BOTO = True
except ImportError:
    HAS_BOTO = False

def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            names={'default': None, 'type': 'list' }
        )
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    asg_names = module.params.get('names')
    if not asg_names:
        asg_names = None

    # Establish connection to AWS EC2 API and query it through boto
    if not HAS_BOTO:
        module.fail_json(msg='boto required for this module')

    region, ec2_url, aws_connect_params = get_aws_connection_info(module)

    if region:
        try:
            connection = connect_to_aws(boto.ec2.autoscale, region, **aws_connect_params)
        except (boto.exception.NoAuthHandlerFound, AnsibleAWSError), e:
            module.fail_json(msg=str(e))
    else:
        module.fail_json(msg="region must be specified")

    all_asgs = connection.get_all_groups(asg_names)

    # Collect results
    results = []
    for asg in all_asgs:
        data = {
            'name': asg.name,
            'availability_zones': asg.availability_zones,
            'default_cooldown': asg.default_cooldown,
            'desired_capacity': asg.desired_capacity,
            'health_check_period': asg.health_check_period,
            'health_check_type': asg.health_check_type,
            'launch_config_name': asg.launch_config_name,
            'load_balancers': asg.load_balancers,
            'max_size': asg.max_size,
            'min_size': asg.min_size,
            'placement_group': asg.placement_group,
            'vpc_zone_identifier': asg.vpc_zone_identifier,
            'termination_policies': asg.termination_policies,
        }
        if getattr(asg, "tags", None):
            data['tags'] = dict((t.key, t.value) for t in asg.tags)
        if asg.instances:
            data['instances'] = [i.instance_id for i in asg.instances]
        results.append(data)

    module.exit_json(asgs=results)

# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import *

if __name__ == '__main__':
    main()

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
module: ec2_group_facts
author: "Stefan Horning (@stefanhorning)"
version_added: "2.2"
short_description: Finds exising EC2 security groups and returns their facts
description:
    - Finds a list of existing EC2 security groups based on given filters. Returns the facts of each found security group.
options:
  name:
    description:
      - Name of the security group.
    required: false
  group_id:
    description:
      - ID of the security group.
    required: false
  description:
    description:
      - Description of the security group.
    required: false
  vpc_id:
    description:
      - ID of the VPC the security belongs to.
    required: false

extends_documentation_fragment:
    - aws
    - ec2

notes:
  - "If no group matches given filters the module will just return an empty list called security_groups: []."
'''

EXAMPLES = '''
- name: Find all EC2 security groups in my VPC
  ec2_group_facts:
    vpc_id: vpc-b4f0exxx
    region: us-east-1
  register: ec2_groups_found

- name: Find all EC2 security groups with name database_server
  ec2_group_facts:
    name: database_server
  register: ec2_groups_found

- name: Find all EC2 security groups with description my database sec group
  ec2_group_facts:
    description: 'my database sec group'
  register: ec2_groups_found

- debug: var=ec2_groups_found.security_groups
'''

RETURN = '''
group_name:
    description: Name of the security group.
    returned: when group is found
    type: string
    sample: "database_server"
group_id:
    description: ID of the security group.
    returned: when group is found
    type: string
    sample: "sg-ded1b2a7"
ip_permissions:
    description: List of incomming port permissions for the security group, list of dictionaries.
    returned: when group is found
    type: list
    sample: "{ ip_protocol: ssh, from_port: 22, to_port: 22, ip_ranges: [], prefix_list_ids: [], user_id_group_pairs: [] }"
ip_permissions_egress:
    description: List of outgoing port permissions for the security group, list of dictionaries.
    returned: when group is found
    type: list
    sample: "{ ip_protocol: ssh, from_port: 22, to_port: 22, ip_ranges: [], prefix_list_ids: [], user_id_group_pairs: [] }"
vpc_id:
    description: ID of the VPC the security group belongs to.
    returned: when group is found
    type: string
    sample: "vpc-b4f0exxx"
owner_id:
    description: The AWS account ID of the security group owner.
    returned: when group is found
    type: string
    sample: 099720109471
description:
    description: Description text of the security group.
    returned: when group is found
    type: string
    sample: "database sec group"
tags:
    description: AWS tags attached to the security group, list of dictionaries.
    returned: when group has tags
    type: list
    sample: { "key": "value" }
'''

try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False


def list_ec2_security_groups(connection, module):
    name = module.params['name']
    description = module.params['description']
    vpc_id = module.params['vpc_id']
    group_id = module.params['group_id']

    # Create filter params
    filter = {}

    if name:
        filter['group-name'] = name
    if description:
        filter['description'] = description
    if vpc_id:
        filter['vpc-id'] = vpc_id
    if group_id:
        filter['group-id'] = group_id

    filters = ansible_dict_to_boto3_filter_list(filter)

    # find groups based on filter
    try:
        groups = connection.describe_security_groups(Filters=filters)
    except ClientError as e:
        module.fail_json(msg=e.message, **camel_dict_to_snake_dict(e.response))

    snaked_groups = []
    for group in groups['SecurityGroups']:
        snaked_groups.append(camel_dict_to_snake_dict(group))

    module.exit_json(security_groups=snaked_groups)

def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
            name=dict(type='str', required=False),
            group_id=dict(type='str', required=False),
            description=dict(type='str', required=False),
            vpc_id=dict(type='str')
        )
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    if not HAS_BOTO3:
        module.fail_json(msg='boto3 required for this module')

    region, ec2_url, aws_connect_params = get_aws_connection_info(module, boto3=True)

    if region:
        connection = boto3_conn(module, conn_type='client', resource='ec2', region=region, endpoint=ec2_url, **aws_connect_params)
    else:
        module.fail_json(msg="region must be specified")

    list_ec2_security_groups(connection, module)

# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import *

if __name__ == '__main__':
    main()

import boto3
import time
import argparse
import sys
from botocore.exceptions import ClientError

#Input: InstanceID string
#Output: AMI.Id string
#Notes: Prints ami.id string to &fd1
def create_ami(instance_id, name):
    ec2 = boto3.resource('ec2')

    # Try and get, if fail do error
    try:
        i = ec2.Instance(instance_id)

        while ec2.Instance(instance_id).state['Name'] != 'stopped':
            if i.state['Name'] == 'running':
                i.stop()
                print(f'Stopping Instance {instance_id}')
            print('Sleeping for 5 Seconds')
            time.sleep(5)
        print(f'Stopped instance {instance_id}')

        ami = i.create_image(Name=name)
        print(f'AMI from instance {instance_id} as {ami.id}')
        return ami.id
    except ClientError:
        print(f"Error: Instance ({instance_id}) Not found")


#Input: Filter map[string]pyobject
#Output: InstanceID string
#Notes:
def get_instance(filter):
    ec2 = boto3.client('ec2')
    instances = ec2.describe_instances(Filters=filter)['Reservations']
    if len(instances) > 1:
        print(f'Too many instances found, need 1, got {len(instances)}') 
        return 0
    else:
        id = instances[0]['Instances'][0]['InstanceId']
        print(f'Found instance {id}')
        return id
    

#Input: map[string]string
#Output: []map[string]pyobject{Name: tags:Key. Values: []string{Value}}...
def format_tags(tags):
    filter = []
    for tag in tags.split(','):
        stag = tag.split(':')
        filter.append({
            'Name': f'tag:{stag[0]}',
            'Values': [stag[1]]
        })
    return filter

#Input: AWS Tag Filter
#Output: AMI-ID
def get_ami(filter):
    ec2 = boto3.client('ec2')
    amis = ec2.describe_images(
        Filters=filter,
    )
    if len(amis['Images']) > 1:
        print(f'Too many images found, need 1, got {len(amis)}') 
        import code; code.interact(local=locals())
        exit(1)
        return 0
    
    ami = amis['Images'][0]['ImageId']
    print(f'Found image {ami}')
    return ami

    
#XXX
def promote_ami(ami, accounts):
    return 0

#Input: AMI-ID and Optional Name
#Output: New AMI-ID
#Notes: If name isn't supplied, it will be the old name + Copy
def copy_ami(ami, name):
    ec2 = boto3.client('ec2')
    if name == None:
        base = boto3.resource('ec2').Image(ami)
        name = base.name + '-copy'

    try:
        id = ec2.copy_image(
            Name = name,
            SourceRegion = 'us-east-1',
            SourceImageId = ami,
        )['ImageId']
        print(f'Copied {ami} => {id}')
        return 1
    except ClientError as e:
        print(f'Error Copying ami: {e}')
        return 0 

#Input: AMI-ID
#Output: Pass/Fail
def delete_ami(ami):
    try:
        base = boto3.resource('ec2').Image(ami)
        base.deregister()
        print(f'Degregistered {base.image_id}')
    except ClientError as e:
        print(f'Error Reaching AWS {e}')
        return False
    except PermissionError as e:
        print(f'Permission Error: {e}')
        return False
    return True

#----ARG WRAPPERS----#
def create_wrapper(args):
    if args.instance and args.name:
        return create_ami(args.instance, args.name)
    elif args.tags and args.name:
        return create_ami(get_instance(format_tags(args.tags)), args.name)
    else:
        print(f'Need Tags or InstanceID and a Name to tag ami')
        return 0


def copy_wrapper(args):
    if args.ami:
        copy_ami(args.ami, args.name)
    elif args.tags:
        copy_ami(get_ami(format_tags(args.tags)), args.name)
    else:
        print(f'Need Tags or AMI-ID')
        return 0
    if args.delete:
        delete_ami(args.ami)
 
def delete_wrapper(args):
    if args.ami:
        delete_ami(args.ami)
    elif args.tags:
        delete_ami(get_ami(format_tags(args.tags)))
    else:
        print(f'Need Tags or AMI-ID')
        return False
    return True
#--------------------#


def main():
    parser = argparse.ArgumentParser(prog='AMI')
    subparser = parser.add_subparsers()

    create = subparser.add_parser('create')
    create.add_argument('-i', '--instance', type=str)
    create.add_argument('-t', '--tags', type=str)
    create.add_argument('--name', required=True)
    create.set_defaults(func=create_wrapper)


    delete = subparser.add_parser('delete', help="Delete an AMI")
    delete.add_argument('--ami', type=str)
    delete.add_argument('-t', '--tags', type=str)
    delete.set_defaults(func=delete_wrapper)


    copy = subparser.add_parser('copy')
    copy.add_argument('--ami')
    copy.add_argument('-t', '--tags', type=str)
    copy.add_argument('--name')
    copy.add_argument('--delete', type=bool)
    copy.set_defaults(func=copy_wrapper)

    arg = parser.parse_args(sys.argv[1:])
    arg.func(arg)

if __name__ == '__main__':
    main()
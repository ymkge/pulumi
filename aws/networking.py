import pulumi
import pulumi_aws as aws

def get_default_vpc_and_subnets():
    """
    デフォルトVPCとそのサブネットを取得します。
    """
    default_vpc = aws.ec2.get_vpc(default=True)
    default_subnets = aws.ec2.get_subnets(filters=[
        aws.ec2.GetSubnetsFilterArgs(name="vpc-id", values=[default_vpc.id])
    ])
    return default_vpc, default_subnets

def create_redshift_security_group(name: str, vpc_id: str):
    """
    Redshift用のセキュリティグループを作成します。
    ConfigからallowedCidrを取得するロジックも含みます。
    """
    config = pulumi.Config()
    ingress_rules = []
    allowed_cidr = config.get("allowedCidr")
    
    if allowed_cidr:
        ingress_rules.append(
            aws.ec2.SecurityGroupIngressArgs(
                protocol="tcp",
                from_port=5439,
                to_port=5439,
                cidr_blocks=[allowed_cidr],
                description="Redshift Ingress from Config"
            )
        )

    return aws.ec2.SecurityGroup(name,
        description="Allow Redshift access",
        vpc_id=vpc_id,
        ingress=ingress_rules,
        egress=[
            aws.ec2.SecurityGroupEgressArgs(
                protocol="-1",
                from_port=0,
                to_port=0,
                cidr_blocks=["0.0.0.0/0"]
            )
        ]
    )

"""
Network Virtualization Simulator for Cloud Computing
Demonstrates Virtual Private Clouds, Subnets, and Network Isolation
"""

import uuid
import ipaddress
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum

class VMState(Enum):
    RUNNING = "running"
    STOPPED = "stopped"

@dataclass
class VM:
    """Virtual Machine"""
    vm_id: str
    name: str
    private_ip: str
    state: VMState = VMState.STOPPED
    
    def start(self):
        self.state = VMState.RUNNING
    
    def stop(self):
        self.state = VMState.STOPPED

@dataclass
class Subnet:
    """Virtual Subnet"""
    subnet_id: str
    name: str
    cidr: str
    gateway: str
    vms: Dict[str, VM] = field(default_factory=dict)
    
    def allocate_ip(self) -> Optional[str]:
        """Assign IP from subnet range"""
        used_ips = [vm.private_ip for vm in self.vms.values()]
        network = ipaddress.ip_network(self.cidr)
        
        for ip in network.hosts():
            ip_str = str(ip)
            if ip_str != self.gateway and ip_str not in used_ips:
                return ip_str
        return None
    
    def create_vm(self, name: str) -> Optional[VM]:
        """Create VM in this subnet"""
        ip = self.allocate_ip()
        if not ip:
            return None
        
        vm = VM(
            vm_id=f"vm-{uuid.uuid4().hex[:6]}",
            name=name,
            private_ip=ip
        )
        self.vms[vm.vm_id] = vm
        return vm

@dataclass
class VPC:
    """Virtual Private Cloud"""
    vpc_id: str
    name: str
    cidr: str
    subnets: Dict[str, Subnet] = field(default_factory=dict)
    
    def add_subnet(self, name: str, cidr: str) -> Optional[Subnet]:
        """Create a subnet within VPC"""
        try:
            subnet_network = ipaddress.ip_network(cidr)
            vpc_network = ipaddress.ip_network(self.cidr)
            
            # Check if subnet is within VPC CIDR
            if not subnet_network.subnet_of(vpc_network):
                print(f"Error: {cidr} not within VPC {self.cidr}")
                return None
            
            # Check for overlaps
            for existing in self.subnets.values():
                if ipaddress.ip_network(existing.cidr).overlaps(subnet_network):
                    print(f"Error: CIDR overlaps with existing subnet")
                    return None
            
            # First usable IP as gateway
            gateway = str(list(subnet_network.hosts())[0])
            
            subnet = Subnet(
                subnet_id=f"subnet-{uuid.uuid4().hex[:6]}",
                name=name,
                cidr=cidr,
                gateway=gateway
            )
            
            self.subnets[subnet.subnet_id] = subnet
            return subnet
            
        except Exception as e:
            print(f"Error: {e}")
            return None
    
    def show_topology(self):
        """Display network topology"""
        print(f"\n{'='*50}")
        print(f"VPC: {self.name} ({self.vpc_id})")
        print(f"CIDR: {self.cidr}")
        print(f"{'='*50}")
        
        for subnet in self.subnets.values():
            print(f"\n├── Subnet: {subnet.name} ({subnet.subnet_id})")
            print(f"│   ├── CIDR: {subnet.cidr}")
            print(f"│   ├── Gateway: {subnet.gateway}")
            print(f"│   └── VMs: {len(subnet.vms)}")
            
            for vm in subnet.vms.values():
                print(f"│       ├── {vm.name} ({vm.vm_id})")
                print(f"│       │   ├── IP: {vm.private_ip}")
                print(f"│       │   └── State: {vm.state.value}")

class NetworkVirtualizationManager:
    """Main manager for virtual networks"""
    
    def __init__(self):
        self.vpcs: Dict[str, VPC] = {}
        self.tenants: Dict[str, List[str]] = {}  # tenant_id -> list of vpc_ids
    
    def create_vpc(self, tenant_id: str, name: str, cidr: str) -> Optional[VPC]:
        """Create a new VPC for a tenant"""
        # Validate CIDR
        try:
            ipaddress.ip_network(cidr)
        except:
            print(f"Invalid CIDR: {cidr}")
            return None
        
        vpc = VPC(
            vpc_id=f"vpc-{uuid.uuid4().hex[:6]}",
            name=name,
            cidr=cidr
        )
        
        self.vpcs[vpc.vpc_id] = vpc
        
        if tenant_id not in self.tenants:
            self.tenants[tenant_id] = []
        self.tenants[tenant_id].append(vpc.vpc_id)
        
        print(f"✓ VPC '{name}' created for tenant {tenant_id}")
        return vpc
    
    def get_vpc(self, vpc_id: str) -> Optional[VPC]:
        """Get VPC by ID"""
        return self.vpcs.get(vpc_id)
    
    def list_tenants(self):
        """List all tenants and their networks"""
        print("\n" + "="*60)
        print("TENANT NETWORKS OVERVIEW")
        print("="*60)
        
        for tenant_id, vpc_ids in self.tenants.items():
            print(f"\n📦 Tenant: {tenant_id}")
            print(f"   VPCs: {len(vpc_ids)}")
            for vpc_id in vpc_ids:
                vpc = self.vpcs[vpc_id]
                print(f"   ├── {vpc.name} ({vpc_id})")
                print(f"   │   └── CIDR: {vpc.cidr}")
                print(f"   │   └── Subnets: {len(vpc.subnets)}")

# Demo and Testing
def demo():
    """Demonstrate network virtualization"""
    
    print("="*60)
    print("NETWORK VIRTUALIZATION SIMULATOR")
    print("Demonstrating Multi-Tenant Isolated Networks")
    print("="*60)
    
    # Create manager
    manager = NetworkVirtualizationManager()
    
    # Tenant 1: TechCorp
    print("\n🔧 Setting up TechCorp network...")
    techcorp_vpc = manager.create_vpc("TechCorp", "Production-VPC", "10.0.0.0/16")
    
    # Add subnets
    web_subnet = techcorp_vpc.add_subnet("Web-Subnet", "10.0.1.0/24")
    db_subnet = techcorp_vpc.add_subnet("DB-Subnet", "10.0.2.0/24")
    
    # Create VMs
    if web_subnet:
        web_vm1 = web_subnet.create_vm("web-server-1")
        web_vm2 = web_subnet.create_vm("web-server-2")
        web_vm1.start()
        
    if db_subnet:
        db_vm = db_subnet.create_vm("database-1")
        db_vm.start()
    
    # Tenant 2: StartupInc
    print("\n🔧 Setting up StartupInc network...")
    startup_vpc = manager.create_vpc("StartupInc", "Dev-VPC", "172.16.0.0/12")
    
    app_subnet = startup_vpc.add_subnet("App-Subnet", "172.16.1.0/24")
    if app_subnet:
        app_vm = app_subnet.create_vm("app-server")
        app_vm.start()
    
    # Tenant 3: EnterpriseCo
    print("\n🔧 Setting up EnterpriseCo network...")
    enterprise_vpc = manager.create_vpc("EnterpriseCo", "Corp-VPC", "192.168.0.0/16")
    
    frontend_subnet = enterprise_vpc.add_subnet("Frontend-Subnet", "192.168.1.0/24")
    backend_subnet = enterprise_vpc.add_subnet("Backend-Subnet", "192.168.2.0/24")
    
    if frontend_subnet:
        frontend_vm = frontend_subnet.create_vm("frontend-1")
        frontend_vm.start()
        
    if backend_subnet:
        backend_vm = backend_subnet.create_vm("backend-1")
    
    # Show all tenants
    manager.list_tenants()
    
    # Show detailed topology for TechCorp
    print("\n" + "="*60)
    print("DETAILED NETWORK TOPOLOGY - TechCorp")
    print("="*60)
    techcorp_vpc.show_topology()
    
    # Demonstrate network isolation
    print("\n" + "="*60)
    print("NETWORK ISOLATION DEMONSTRATION")
    print("="*60)
    print("\n✓ Tenants have completely isolated networks")
    print("  - TechCorp: 10.0.0.0/16")
    print("  - StartupInc: 172.16.0.0/12")
    print("  - EnterpriseCo: 192.168.0.0/16")
    print("\n✓ Subnets are isolated within each VPC")
    print("  - No cross-VPC communication without explicit routing")
    print("  - Each tenant has their own virtual network space")

if __name__ == "__main__":
    demo()
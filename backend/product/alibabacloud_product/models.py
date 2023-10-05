from django.utils import timezone
from django.db import models
from project.models import Project
from abc import abstractmethod
import logging

logger = logging.getLogger('clouddog')


class ProductType(models.TextChoices):
    ECS = ('ecs', '服务器')
    WAF = ('waf', 'Web应用防火墙')
    SLB = ('slb', '负载均衡')
    ALB = ('alb', '应用型负载均衡')
    EIP = ('eip', '弹性公网IP')
    SSL = ('ssl', 'SSL证书')
    CSC = ('csc', '云安全中心')

    class Meta:
        app_label = 'ProductType'


class ProductBaseModel(models.Model):
    api_request_id = models.CharField(primary_key=True, default='', max_length=100, db_comment='API Request Id')
    instance_id = models.CharField(default='', max_length=50, verbose_name='InstanceId', db_comment='实例ID')
    request_time = models.DateTimeField(default=timezone.now, max_length=30, verbose_name='RequestTime', db_comment='API请求时间')
    product_type = models.CharField(default=ProductType.ECS.value, max_length=100, verbose_name='ProductType', db_comment='云产品类型', choices=ProductType.choices)
    project_name = models.CharField(default='', max_length=30, verbose_name='Project Name', db_comment='项目名称')
    project = models.ForeignKey(
        to="project.Project",  # which table
        to_field="id",  # which column in table
        # https://foofish.net/django-foreignkey-on-delete.html
        on_delete=models.CASCADE,  # When a project is deleted, all products belonging to that project will be deleted
        related_name='productInProject'  # query a product info from project: project.productInProject.all()
    )

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    class Meta:
        abstract = True
        app_label = 'ProductBasicInfo'

    @abstractmethod
    def get_basic_info(self):
        pass


class AlibabacloudEcsApiResponse(ProductBaseModel):
    Status = (
        ('Pending', '创建中'),
        ('Running', '运行中'),
        ('Starting', '启动中'),
        ('Stopping', '停止中'),
        ('Stopped', '已停止'),
    )
    LockReason = (
        ('financial', '因欠费被锁定'),
        ('security', '因安全原因被锁定'),
        ('Recycling', '抢占式实例的待释放锁定状态'),
        ('dedicatedhostfinancial', '因为专有宿主机欠费导致ECS实例被锁定'),
        ('refunded', '因退款被锁定'),
    )
    InternetChargeType = (
        ('PayByBandwidth', '按固定带宽计费'),
        ('PayByTraffic', '按使用流量计费'),
    )
    InstanceChargeType = (
        ('PostPaid', '按量付费'),
        ('PrePaid', '包年包月')
    )
    StoppedMode = (
        ('KeepCharging', '停机后继续收费，为您继续保留库存资源'),
        ('StopCharging', '停机后不收费。停机后，我们释放实例对应的资源，例如vCPU、内存和公网IP等资源。重启是否成功依赖于当前地域中是否仍有资源库存'),
        ('Not-applicable', '本实例不支持停机不收费功能'),
    )
    RenewalStatus = (
        ('AutoRenewal', '自动续费'),
        ('Normal', '非自动续费'),
        ('NotRenewal', '不再续费'),
    )
    project = models.ForeignKey(
        to="project.Project",
        to_field="id",
        on_delete=models.CASCADE,
        related_name='ECSInProject'
    )

    """ ECS Instance Property """
    product_type = models.CharField(default=ProductType.ECS.value, max_length=70, verbose_name='ProductType', db_comment='云产品类型', choices=ProductType.choices)
    auto_renew_enabled = models.BooleanField(default=True, verbose_name='AutoRenewEnabled', db_comment='是否已开启自动续费功能')
    instance_name = models.CharField(default='', max_length=30, verbose_name='InstanceName', db_comment='实例的自定义名称')
    renewal_status = models.CharField(default='', max_length=30, verbose_name='RenewalStatus', db_comment='实例的自动续费状态', choices=RenewalStatus)
    period_init = models.CharField(default='', max_length=20, verbose_name='PeriodUnit', db_comment='自动续费时长的单位')
    duration = models.IntegerField(default=0, verbose_name='Duration', db_comment='自动续费时长')
    region_id = models.CharField(default='', max_length=30, verbose_name='RegionId', db_comment='实例地域')
    ecs_status = models.CharField(default='', max_length=20, verbose_name='EcsStatus', db_comment='实例状态', choices=Status)
    instance_charge_type = models.CharField(default='', max_length=30, verbose_name='InstanceChargeType', db_comment='实例付费类型', choices=InstanceChargeType)
    internet_charge_type = models.CharField(default='', max_length=30, verbose_name='InternetChargeType', db_comment='按固定带宽/使用流量计费', choices=InternetChargeType)
    expired_time = models.CharField(default='', max_length=30, verbose_name='ExpiredTime', db_comment='过期时间')
    stopped_mode = models.CharField(default='', max_length=30, verbose_name='StoppedMode', db_comment='实例停机后是否继续收费', choices=StoppedMode)
    start_time = models.CharField(default='', max_length=50, verbose_name='StartTime', db_comment='实例最近一次的启动时间')
    auto_release_time = models.CharField(default='', max_length=50, verbose_name='AutoReleaseTime', db_comment='按量付费实例的自动释放时间')
    lock_reason = models.CharField(default='', max_length=30, verbose_name='LockReason', db_comment='实例的锁定原因', choices=LockReason)

    def get_basic_info(self):
        to_string = 'ECS LOG: {} \'s instance {} in {} status is {}'.format(self.project_name, self.instance_name, self.region_id, self.ecs_status)
        return to_string

    class Meta:
        db_table = 'alibabacloud_ecs_api_response'


class AlibabacloudWafApiResponse(ProductBaseModel):
    Status = (
        (1, '表示正常'),
        (2, '表示到期'),
        (3, '表示释放'),
    )
    Edition = (
        ('Basic', '基础版'),
        ('Pro', '高级版'),
        ('Business', '企业版'),
        ('Enterprise', '旗舰版'),
    )
    Region = (
        ('cn-hangzhou', '表示中国内地'),
        ('ap-southeast-1', '表示非中国内地'),
    )
    PayType = (
        ('POSTPAY', '已开通按量付费WAF实例'),
        ('PREPAY', '表示已开通包年包月WAF实例'),
    )
    InDebt = (
        (1, '表示已欠费'),
        (0, '表示正常'),
    )
    project = models.ForeignKey(
        to="project.Project",
        to_field="id",
        on_delete=models.CASCADE,
        related_name='WAFInProject'
    )

    """ WAF Instance Property """
    product_type = models.CharField(default=ProductType.WAF.value, max_length=70, verbose_name='ProductType', db_comment='云产品类型', choices=ProductType.choices)
    waf_status = models.IntegerField(default=None, verbose_name='WafStatus', db_comment='WAF实例的当前状态', choices=Status)
    end_time = models.BigIntegerField(default=None, verbose_name='EndDate', db_comment='WAF实例的到期时间')
    edition = models.CharField(default='', max_length=40, verbose_name='Edition', db_comment='WAF实例的版本', choices=Edition)
    region = models.CharField(default='', max_length=30, verbose_name='Region', db_comment='WAF实例的地域', choices=Region)
    pay_type = models.CharField(default=None, verbose_name='PayType', db_comment='WAF实例的付费类型', choices=PayType)
    in_debt = models.IntegerField(default=0, verbose_name='InDebt', db_comment='WAF实例是否存在欠费', choices=InDebt)
    start_time = models.BigIntegerField(default=None, verbose_name='StartTime', db_comment='购买时间')

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    def get_basic_info(self):
        to_string = 'WAF LOG: {} \'s instance {} in {} status is {}'.format(self.project_name, self.instance_id, self.region, self.waf_status)
        return to_string

    class Meta:
        db_table = 'alibabacloud_waf_api_response'


class AlibabacloudSLBApiResponse(ProductBaseModel):
    LoadBalancerStatus = (
        ('inactive', '实例已停止'),
        ('active', '实例运行中'),
        ('locked', '实例已锁定'),
    )
    PayType = (
        ('PayOnDemand', '按量付费'),
        ('PrePay', '包年包月'),
    )
    AddressType = (
        ('internet', '公网负载均衡'),
        ('intranet', '内网负载均衡'),
    )
    AddressIPVersion = (
        ('ipv4', 'ipv4'),
        ('ipv6', 'ipv6'),
    )
    InternetChargeType = (
        (3, '按带宽计费'),
        (4, '按流量计费'),
    )
    # 该参数仅适用于中国站且当PayType（实例付费模式）取值为PayOnDemand（按量付费）时，该参数生效。
    InstanceChargeType = (
        ('PayBySpec', '按规格计费'),
        ('PayByCLCU', '按使用量计费'),
    )
    RenewalStatus = (
        ('AutoRenewal', '自动续费'),
        ('Normal', '非自动续费'),
        ('NotRenewal', '不再续费'),
    )
    RenewalCycUnit = (
        ('Year', '年'),
        ('Month', '月'),
    )
    project = models.ForeignKey(
        to="project.Project",
        to_field="id",
        on_delete=models.CASCADE,
        related_name='SLBInProject'
    )

    """ SLB Instance Property """
    product_type = models.CharField(default=ProductType.SLB.value, max_length=70, verbose_name='ProductType', db_comment='云产品类型', choices=ProductType.choices)
    create_time = models.CharField(default=None, verbose_name='CreateTime', db_comment='实例创建时间')
    pay_type = models.CharField(default=None, verbose_name='PayType', db_comment='负载均衡实例付费模式', choices=PayType)
    internet_charge_type = models.CharField(default=None, verbose_name='InternetChargeType', db_comment='公网类型实例付费方式', choices=InternetChargeType)
    load_balancer_name = models.CharField(default='', max_length=50, verbose_name='LoadBalancerName', db_comment='负载均衡实例的名称')
    address = models.CharField(default='1.1.1.1', max_length=100, verbose_name='Address', db_comment='负载均衡实例服务地址')
    address_type = models.CharField(default='internet', max_length=100, verbose_name='AddressType', db_comment='实例的网络类型', choices=AddressType)
    address_ip_version = models.CharField(default='ipv4', max_length=100, verbose_name='AddressIPVersion', db_comment='IP版本', choices=AddressIPVersion)
    region_id = models.CharField(default='', max_length=100, verbose_name='RegionId', db_comment='负载均衡实例的地域ID')
    load_balancer_status = models.CharField(default=None, max_length=100, verbose_name='LoadBalancerStatus', db_comment='负载均衡实例状态', choices=LoadBalancerStatus)
    load_balancer_spec = models.CharField(default=None, max_length=100, verbose_name='LoadBalancerSpec', db_comment='负载均衡实例的性能规格')
    instance_charge_type = models.CharField(default=None, max_length=100, verbose_name='InstanceChargeType', db_comment='实例计费方式', choices=InstanceChargeType)
    master_zone_id = models.CharField(default=None, max_length=50, verbose_name='MasterZoneId', db_comment='实例的主可用区')
    slave_zone_id = models.CharField(default=None, max_length=50, verbose_name='SlaveZoneId', db_comment='实例的备可用区')

    # detail
    bandwidth = models.IntegerField(default=0, verbose_name='Bandwidth', db_comment='按带宽计费的公网型实例的带宽峰值')
    end_time_stamp = models.BigIntegerField(default=3249380160000, verbose_name='EndTimeStamp', db_comment='传统型负载均衡实例结束时间戳')
    end_time = models.CharField(default='', max_length=50, verbose_name='EndTime', db_comment='传统型负载均衡实例结束时间')
    auto_release_time = models.BigIntegerField(default=3249380160000, verbose_name='AutoReleaseTime', db_comment='释放时间的时间戳')
    renewal_status = models.CharField(default='', max_length=50, verbose_name='RenewalStatus', db_comment='续费状态', choices=RenewalStatus)
    renewal_duration = models.IntegerField(default=0, verbose_name='RenewalDuration', db_comment='自动续费时长')
    renewal_cyc_unit = models.CharField(null=True, blank=True, default='Month', max_length=50, verbose_name='RenewalCycUnit', db_comment='自动续费周期', choices=RenewalCycUnit)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    def get_basic_info(self):
        to_string = 'SLB LOG: {} \'s instance {} in {} status is {}'.format(self.project_name, self.instance_id, self.region_id, self.load_balancer_status)
        return to_string

    class Meta:
        db_table = 'alibabacloud_slb_api_response'


class AlibabacloudALBApiResponse(ProductBaseModel):
    LoadBalancerBussinessStatus = (
        ('Abnormal', '异常'),
        ('Normal', '正常'),
    )
    PayType = (
        ('PostPay', '按量付费'),
        ('PrePay', '包年包月'),
    )
    AddressType = (
        ('internet', '公网负载均衡'),
        ('intranet', '内网负载均衡'),
    )
    AddressIpVersion = (
        ('Ipv4', 'IPv4类型'),
        ('DualStack', '双栈类型'),
    )
    AddressAllocatedMode = (
        ('Fixed', '固定IP模式'),
        ('Dynamic', '动态IP模式'),
    )
    Ipv6AddressType = (
        ('Internet', '公网'),
        ('Intranet', '私网'),
    )
    LoadBalancerEdition = (
        ('Basic', '基础版'),
        ('Standard', '标准版'),
        ('StandardWithWaf', 'WAF增强版'),
    )
    LoadBalancerStatus = (
        ('Inactive', '已停止'),
        ('Active', '运行中'),
        ('Provisioning', '创建中'),
        ('Configuring', '变配中'),
        ('CreateFailed', '创建失败'),
    )
    project = models.ForeignKey(
        to="project.Project",
        to_field="id",
        on_delete=models.CASCADE,
        related_name='ALBInProject'
    )

    """ ALB Instance Property """
    product_type = models.CharField(default=ProductType.ALB.value, max_length=70, verbose_name='ProductType', db_comment='云产品类型', choices=ProductType.choices)
    create_time = models.CharField(default=None, verbose_name='CreateTime', db_comment='实例创建时间')

    address_allocated_mode = models.CharField(default='Fixed', max_length=50, verbose_name='AddressAllocatedMode', db_comment='地址模式', choices=AddressAllocatedMode)
    address_type = models.CharField(default='internet', max_length=100, verbose_name='AddressType', db_comment='实例的网络类型', choices=AddressType)
    dns_name = models.CharField(default='', max_length=200, verbose_name='DNSName', db_comment='DNS域名')
    pay_type = models.CharField(default='PostPay', verbose_name='PayType', db_comment='负载均衡实例付费模式', choices=PayType)
    load_balancer_bussiness_status = models.CharField(default=None, max_length=100, verbose_name='LoadBalancerBussinessStatus', db_comment='负载均衡的业务状态', choices=LoadBalancerBussinessStatus)
    load_balancer_edition = models.CharField(default='Basic', max_length=50, verbose_name='LoadBalancerEdition', db_comment='负载均衡的版本', choices=LoadBalancerEdition)
    load_balancer_name = models.CharField(default='', max_length=50, verbose_name='LoadBalancerName', db_comment='负载均衡实例的名称')
    load_balancer_status = models.CharField(default='Active', max_length=50, verbose_name='LoadBalancerStatus', db_comment='实例状态', choices=LoadBalancerStatus)
    address_ip_version = models.CharField(default='ipv4', max_length=50, verbose_name='AddressIpVersion', db_comment='IP版本', choices=AddressIpVersion)
    ipv6_address_type = models.CharField(default='-', max_length=50, verbose_name='Ipv6AddressType', db_comment='应用型负载均衡IPv6的网络地址类型', choices=Ipv6AddressType)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    def get_basic_info(self):
        to_string = 'ALB LOG: {} \'s instance {} status is {}'.format(self.project_name, self.instance_id, self.load_balancer_status)
        return to_string

    class Meta:
        db_table = 'alibabacloud_alb_api_response'


class AlibabacloudEIPApiResponse(ProductBaseModel):
    ReservationInternetChargeType = (
        ('PayByBandwidth', '按固定带宽计费'),
        ('PayByTraffic', '按使用流量计费'),
    )
    BusinessStatus = (
        ('Normal', '正常'),
        ('FinancialLocked', '被锁定'),
    )
    ChargeType = (
        ('PostPaid', '按量计费'),
        ('PrePaid', '包年包月'),
    )
    EIPStatus = (
        ('Associating', '绑定中'),
        ('Unassociating', '解绑中'),
        ('InUse', '已分配'),
        ('Available', '可用'),
        ('Releasing', '释放中'),
    )
    project = models.ForeignKey(
        to="project.Project",
        to_field="id",
        on_delete=models.CASCADE,
        related_name='EIPInProject'
    )

    """ EIP Instance Property """
    product_type = models.CharField(default=ProductType.EIP.value, max_length=70, verbose_name='ProductType', db_comment='云产品类型', choices=ProductType.choices)
    name = models.CharField(default='', max_length=50, verbose_name='Name', db_comment='EIP的名称')
    region_id = models.CharField(default='', max_length=50, verbose_name='RegionId', db_comment='EIP所在的地域ID')
    expired_time = models.CharField(default='', max_length=50, verbose_name='ExpiredTime', db_comment='到期时间')
    allocation_id = models.CharField(default='', max_length=50, verbose_name='AllocationId', db_comment='EIP的实例ID')
    instance_id = models.CharField(default='', max_length=50, verbose_name='InstanceId', db_comment='当前绑定的实例的ID')
    instance_type = models.CharField(default='', max_length=50, verbose_name='InstanceType', db_comment='当前绑定的实例类型')
    internet_charge_type = models.CharField(default='', max_length=50, verbose_name='InternetChargeType', db_comment='EIP的计费方式', choices=BusinessStatus)
    business_status = models.CharField(default='', max_length=50, verbose_name='BusinessStatus', db_comment='EIP实例的业务状态', choices=BusinessStatus)
    reservation_bandwidth = models.CharField(default='internet', max_length=10, verbose_name='ReservationBandwidth', db_comment='续费带宽-单位:Mbps')
    bandwidth = models.CharField(default='', max_length=10, verbose_name='Bandwidth', db_comment='EIP的带宽峰值')
    ip_address = models.CharField(default='1.1.1.1', max_length=30, verbose_name='IpAddress', db_comment='EIP的IP地址')
    reservation_internet_charge_type = models.CharField(default='PayByTraffic', max_length=100, verbose_name='ReservationInternetChargeType', db_comment='续费付费类型', choices=ReservationInternetChargeType)
    charge_type = models.CharField(default='Basic', max_length=50, verbose_name='ChargeType', db_comment='EIP的付费模式', choices=ChargeType)
    net_mode = models.CharField(default='public', max_length=50, verbose_name='Netmode', db_comment='网络类型')
    allocation_time = models.CharField(default='', max_length=100, verbose_name='AllocationTime', db_comment='EIP的创建时间')
    status = models.CharField(default='ipv4', max_length=50, verbose_name='Status', db_comment='EIP的状态', choices=EIPStatus)
    reservation_active_time = models.CharField(default='', max_length=100, verbose_name='ReservationActiveTime', db_comment='续费生效时间')

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    def get_basic_info(self):
        to_string = 'EIP LOG: {} \'s instance {} status is {}'.format(self.project_name, self.instance_id, self.status)
        return to_string

    class Meta:
        db_table = 'alibabacloud_eip_api_response'


class AlibabacloudSSLApiResponse(ProductBaseModel):
    Status = (
        ('ISSUE', '表示正常签发'),
        ('REVOKE', '表示已被吊销'),
    )
    project = models.ForeignKey(
        to="project.Project",
        to_field="id",
        on_delete=models.CASCADE,
        related_name='SSLInProject'
    )

    """ SSL Instance Property """
    product_type = models.CharField(default=ProductType.SSL.value, max_length=70, verbose_name='ProductType', db_comment='云产品类型', choices=ProductType.choices)
    subject_dn = models.CharField(default='', max_length=50, verbose_name='SubjectDN', db_comment='证书的Distinguished_Name属性')
    common_name = models.CharField(default='', max_length=50, verbose_name='CommonName', db_comment='证书的公用名')
    organization_unit = models.CharField(default='', max_length=50, verbose_name='OrganizationUnit', db_comment='签发该证书的子CA证书关联的组织机构下部门的名称')
    organization = models.CharField(default='', max_length=50, verbose_name='Organization', db_comment='签发该证书的子CA证书关联的组织机构的名称')
    status = models.CharField(default='ISSUE', max_length=50, verbose_name='Status', db_comment='证书的状态', choices=Status)
    before_date = models.BigIntegerField(default=0, verbose_name='BeforeDate', db_comment='证书的签发日期')
    after_date = models.BigIntegerField(default=0, verbose_name='AfterDate', db_comment='证书的到期日期')
    days = models.IntegerField(default=0, verbose_name='Days', db_comment='证书的有效期')

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    def get_basic_info(self):
        to_string = 'SSL LOG: {} \'s instance {} status is {}'.format(self.project_name, self.instance_id, self.status)
        return to_string

    class Meta:
        db_table = 'alibabacloud_ssl_api_response'


class AlibabacloudCSCApiResponse(ProductBaseModel):
    Status = (
        (0, '未购买'),
        (1, '已购买'),
    )
    IsEnabled = (
        (0, '未开启'),
        (1, '已开启'),
    )
    Version = (
        (1, '免费版'),
        (3, '企业版'),
        (5, '高级版'),
        (6, '防病毒版'),
        (7, '旗舰版'),
        (8, '多版本'),
        (10, '仅采购增值服务'),
    )
    project = models.ForeignKey(
        to="project.Project",
        to_field="id",
        on_delete=models.CASCADE,
        related_name='CSCInProject'
    )

    """ CSC Instance Property """
    product_type = models.CharField(default=ProductType.CSC.value, max_length=70, verbose_name='ProductType', db_comment='云产品类型', choices=ProductType.choices)
    mv_auth_count = models.IntegerField(default=0, verbose_name='MVAuthCount', db_comment='购买多版本时的总授权数')
    sas_log = models.IntegerField(default=0, verbose_name='SasLog', db_comment='是否已购买日志分析', choices=Status)
    sas_screen = models.IntegerField(default=0, verbose_name='SasScreen', db_comment='是否已购买安全大屏', choices=Status)
    honeypot_capacity = models.IntegerField(default=0, verbose_name='HoneypotCapacity', db_comment='蜜罐的台数')
    mv_unused_auth_count = models.IntegerField(default=0, verbose_name='MVUnusedAuthCount', db_comment='购买多版本时总剩余授权数')
    web_lock = models.IntegerField(default=0, verbose_name='WebLock', db_comment='是否开启了网页防篡改服务', choices=IsEnabled)
    app_white_list_auth_count = models.IntegerField(default=0, verbose_name='AppWhiteListAuthCount', db_comment='应用白名单授权数')
    last_trail_end_time = models.BigIntegerField(default=0, verbose_name='LastTrailEndTime', db_comment='上一次试用的截止时间戳')
    version = models.IntegerField(default=0, verbose_name='Version', db_comment='云安全中心版本', choices=Version)
    web_lock_auth_count = models.IntegerField(default=0, verbose_name='WebLockAuthCount', db_comment='已购买的网页防篡改的授权数')
    release_time = models.BigIntegerField(default=0, verbose_name='ReleaseTime', db_comment='云安全中心实例释放时间戳')
    highest_version = models.IntegerField(default=0, verbose_name='HighestVersion', db_comment='购买安全中心最高版本', choices=Version)
    asset_level = models.IntegerField(default=0, verbose_name='AssetLevel', db_comment='已购买的服务器授权数')
    is_over_balance = models.BooleanField(default=False, verbose_name='IsOverBalance', db_comment='现有服务器台数是否超过购买的最大授权数')
    sls_capacity = models.IntegerField(default=0, verbose_name='SlsCapacity', db_comment='已购买的日志存储容量GB')
    vm_cores = models.IntegerField(default=0, verbose_name='VmCores', db_comment='已购买的授权核数')
    allow_partial_buy = models.IntegerField(default=1, verbose_name='AllowPartialBuy', db_comment='是否允许按量购买')
    app_white_list = models.IntegerField(default=0, verbose_name='AppWhiteList', db_comment='是否开启应用白名单')  # 0：未开启 2：已开启
    image_scan_capacity = models.IntegerField(default=0, verbose_name='ImageScanCapacity', db_comment='镜像扫描授权数')
    is_trial_version = models.IntegerField(default=0, verbose_name='IsTrialVersion', db_comment='是否是试用版本')  # 0：非试用版本 1：试用版本
    user_defined_alarms = models.IntegerField(default=0, verbose_name='UserDefinedAlarms', db_comment='是否开启自定义告警功能')  # 0：未开启 2：已开启
    open_time = models.BigIntegerField(default=0, verbose_name='OpenTime', db_comment='开通服务时间戳')  # 0：未开启 2：已开启
    is_new_container_version = models.BooleanField(default=False, verbose_name='IsNewContainerVersion', db_comment='是否是新旗舰版')
    is_new_multi_version = models.BooleanField(default=False, verbose_name='IsNewMultiVersion', db_comment='是否是新多版本')
    threat_analysis_capacity = models.IntegerField(default=0, verbose_name='ThreatAnalysisCapacity', db_comment='威胁分析容量GB')
    cspm_capacity = models.IntegerField(default=0, verbose_name='CspmCapacity', db_comment='云平台配置检查扫描数')
    vul_fix_capacity = models.IntegerField(default=0, verbose_name='VulFixCapacity', db_comment='漏洞修复数n次/月')
    rasp_capacity = models.IntegerField(default=0, verbose_name='RaspCapacity', db_comment='应用防护数n个/月')

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    def get_basic_info(self):
        to_string = 'CSC LOG: {} \'s instance {} status is {}'.format(self.project_name, self.instance_id, self.status)
        return to_string

    class Meta:
        db_table = 'alibabacloud_csc_api_response'

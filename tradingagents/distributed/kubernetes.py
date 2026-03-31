# -*- coding: utf-8 -*-
"""
Kubernetes 部署配置

生成 K8s Deployment/Service/ConfigMap YAML
"""

import yaml
import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime


@dataclass
class ContainerConfig:
    """容器配置"""
    name: str = "trading-agent"
    image: str = "tradingagents-cn:latest"
    port: int = 8000
    env: Dict[str, str] = field(default_factory=dict)
    resources: Dict[str, Any] = field(default_factory=dict)
    volume_mounts: List[Dict] = field(default_factory=list)


@dataclass
class DeploymentConfig:
    """部署配置"""
    name: str = "trading-agents"
    namespace: str = "default"
    replicas: int = 2
    container: ContainerConfig = field(default_factory=ContainerConfig)
    
    # 服务配置
    service_type: str = "ClusterIP"  # ClusterIP/NodePort/LoadBalancer
    service_port: int = 8000
    
    # 配置
    config_maps: Dict[str, Dict] = field(default_factory=dict)
    secrets: Dict[str, str] = field(default_factory=dict)
    
    # 健康检查
    liveness_probe: Dict = field(default_factory=dict)
    readiness_probe: Dict = field(default_factory=dict)
    
    # 亲和性
    node_selector: Dict[str, str] = field(default_factory=dict)
    tolerations: List[Dict] = field(default_factory=list)


class K8sDeployment:
    """
    Kubernetes 部署生成器
    
    生成 Deployment、Service、ConfigMap YAML
    """
    
    def __init__(self, config: Optional[DeploymentConfig] = None):
        self.config = config or DeploymentConfig()
    
    def _make_deployment(self) -> Dict:
        """生成 Deployment YAML"""
        container = self.config.container
        
        # 资源限制
        resources = container.resources or {
            'limits': {'cpu': '1000m', 'memory': '2Gi'},
            'requests': {'cpu': '250m', 'memory': '512Mi'}
        }
        
        # 环境变量
        env = []
        for key, value in container.env.items():
            env.append({'name': key, 'value': value})
        
        # 健康检查
        liveness = self.config.liveness_probe or {
            'httpGet': {'path': '/health', 'port': container.port},
            'initialDelaySeconds': 30,
            'periodSeconds': 10
        }
        
        readiness = self.config.readiness_probe or {
            'httpGet': {'path': '/ready', 'port': container.port},
            'initialDelaySeconds': 5,
            'periodSeconds': 5
        }
        
        deployment = {
            'apiVersion': 'apps/v1',
            'kind': 'Deployment',
            'metadata': {
                'name': self.config.name,
                'namespace': self.config.namespace,
                'labels': {
                    'app': self.config.name,
                    'version': 'v1'
                }
            },
            'spec': {
                'replicas': self.config.replicas,
                'selector': {
                    'matchLabels': {'app': self.config.name}
                },
                'template': {
                    'metadata': {
                        'labels': {'app': self.config.name}
                    },
                    'spec': {
                        'containers': [{
                            'name': container.name,
                            'image': container.image,
                            'ports': [{
                                'containerPort': container.port,
                                'name': 'http'
                            }],
                            'env': env,
                            'resources': resources,
                            'volumeMounts': container.volume_mounts,
                            'livenessProbe': liveness,
                            'readinessProbe': readiness
                        }],
                        'nodeSelector': self.config.node_selector,
                        'tolerations': self.config.tolerations
                    }
                }
            }
        }
        
        return deployment
    
    def _make_service(self) -> Dict:
        """生成 Service YAML"""
        service = {
            'apiVersion': 'v1',
            'kind': 'Service',
            'metadata': {
                'name': f"{self.config.name}-svc",
                'namespace': self.config.namespace,
                'labels': {'app': self.config.name}
            },
            'spec': {
                'type': self.config.service_type,
                'selector': {'app': self.config.name},
                'ports': [{
                    'port': self.config.service_port,
                    'targetPort': self.config.container.port,
                    'name': 'http'
                }]
            }
        }
        return service
    
    def _make_configmaps(self) -> List[Dict]:
        """生成 ConfigMap YAML 列表"""
        configmaps = []
        
        for name, data in self.config.config_maps.items():
            configmap = {
                'apiVersion': 'v1',
                'kind': 'ConfigMap',
                'metadata': {
                    'name': f"{self.config.name}-{name}",
                    'namespace': self.config.namespace
                },
                'data': data
            }
            configmaps.append(configmap)
        
        return configmaps
    
    def _make_secrets(self) -> List[Dict]:
        """生成 Secret YAML 列表"""
        # 注意：values 需要 base64 编码
        import base64
        
        secrets = []
        
        for name, data in self.config.secrets.items():
            # base64 编码
            encoded_data = {
                key: base64.b64encode(value.encode()).decode()
                for key, value in data.items()
            }
            
            secret = {
                'apiVersion': 'v1',
                'kind': 'Secret',
                'metadata': {
                    'name': f"{self.config.name}-{name}",
                    'namespace': self.config.namespace
                },
                'type': 'Opaque',
                'data': encoded_data
            }
            secrets.append(secret)
        
        return secrets
    
    def generate_yaml(self) -> str:
        """生成完整 YAML（多文档）"""
        docs = []
        
        # ConfigMaps
        docs.extend(self._make_configmaps())
        
        # Secrets
        docs.extend(self._make_secrets())
        
        # Deployment
        docs.append(self._make_deployment())
        
        # Service
        docs.append(self._make_service())
        
        # 生成多文档 YAML
        output = ""
        for i, doc in enumerate(docs):
            if i > 0:
                output += "---\n"
            output += yaml.dump(doc, default_flow_style=False, allow_unicode=True)
        
        return output
    
    def generate_json(self) -> str:
        """生成 JSON 格式"""
        return json.dumps({
            'deployment': self._make_deployment(),
            'service': self._make_service(),
            'configmaps': self._make_configmaps(),
            'secrets': self._make_secrets()
        }, indent=2, ensure_ascii=False)
    
    def save_yaml(self, path: str):
        """保存 YAML 文件"""
        with open(path, 'w', encoding='utf-8') as f:
            f.write(self.generate_yaml())
        print(f"K8s 配置已保存: {path}")
    
    def save_json(self, path: str):
        """保存 JSON 文件"""
        with open(path, 'w', encoding='utf-8') as f:
            f.write(self.generate_json())
        print(f"K8s 配置已保存: {path}")


# 示例用法
def create_example_deployment() -> K8sDeployment:
    """创建示例部署配置"""
    config = DeploymentConfig(
        name="trading-agents",
        namespace="quant",
        replicas=3,
        container=ContainerConfig(
            name="agent",
            image="tradingagents-cn:v1.0",
            port=8000,
            env={
                "LOG_LEVEL": "INFO",
                "REDIS_URL": "redis://redis:6379",
                "DATA_SOURCE": "akshare"
            },
            resources={
                'limits': {'cpu': '2000m', 'memory': '4Gi'},
                'requests': {'cpu': '500m', 'memory': '1Gi'}
            }
        ),
        service_type="LoadBalancer",
        service_port=8000,
        config_maps={
            'strategy': {
                'max_positions.yaml': 'max_positions: 10',
                'risk_limits.yaml': 'max_drawdown: 0.2'
            }
        },
        node_selector={
            'disktype': 'ssd'
        }
    )
    
    return K8sDeployment(config)
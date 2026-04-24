配置系统 API
==============

.. module:: tradingagents.config

集中配置管理，支持配置文件和环境变量。

快速开始
--------

.. code-block:: python

    from tradingagents.config import Settings
    
    # 加载配置
    settings = Settings.load("config.json")
    
    # 访问配置
    api_key = settings.api.api_key
    db_url = settings.database.url
    
    # 保存配置
    settings.save("config.json")

配置类
------

Settings
~~~~~~~~

.. autoclass:: tradingagents.config.Settings
   :members:
   :undoc-members:
   :special-members: __init__

APISettings
~~~~~~~~~~~

.. autoclass:: tradingagents.config.APISettings
   :members:
   :undoc-members:
   :special-members: __init__, from_env

DatabaseSettings
~~~~~~~~~~~~~~~~

.. autoclass:: tradingagents.config.DatabaseSettings
   :members:
   :undoc-members:
   :special-members: __init__, from_env

StrategySettings
~~~~~~~~~~~~~~~~

.. autoclass:: tradingagents.config.StrategySettings
   :members:
   :undoc-members:
   :special-members: __init__, from_dict

LogSettings
~~~~~~~~~~~

.. autoclass:: tradingagents.config.LogSettings
   :members:
   :undoc-members:
   :special-members: __init__, from_dict, from_env

配置优先级
----------

1. 环境变量（有值时覆盖配置文件）
2. 配置文件（如存在）
3. 默认值（代码中定义的dataclass默认值）

2. kubectl 使用备忘手册
=======================

1. 设置快捷别名
---------------

有一些命令的使用频率非常高，可以为其设置短一点的别名，提高输入效率。

::

   alias kc="kubectl"
   alias ka="kubectl apply -f"
   alias kd="kubectl delete -f"

2. 设置自动补全
---------------

想进一步提高输入效率，那么自动补全也少不了。

.. code:: bash

   # 在 bash 中设置当前 shell 的自动补全，要先安装 bash-completion 包。
   source <(kubectl completion bash) 

   # 在您的 bash shell 中永久的添加自动补全
   echo "source <(kubectl completion bash)" >> ~/.bashrc 

设置完后，你使用 kubectl 就可以自动补全一些子命令。

3. 别名也设置补全
-----------------

上面的自动补全只适用于 kubectl
原生命令，若要想让别名命令也能使用补全，需要执行如下命令

.. code:: bash

   complete -F __start_kubectl kc

4. 简洁输出与更多输出
---------------------

简洁输出
~~~~~~~~

只打印名称，不打印其他任何内容

.. code:: bash

   # 获取所有 namespace 下的 pod 名字
   kubectl get pods -A -o=name

更多输出
~~~~~~~~

.. code:: bash

   # 包含 ip node 等信息
   kubectl get pods -o wide

   # 包含 ip role 等信息
   kubectl get nodes -o wide

   # 在 wide 基础上再显示标签
   kubectl get no -o wide --show-labels

5. 高级输出 之 格式
-------------------

yaml
~~~~

.. code:: bash

   # 打印 nginx  pod 的详细配置，并以 yaml 格式输出
   kubectl get pods nginx -o yaml

json
~~~~

.. code:: bash

   # 打印 nginx  pod 的详细配置，并以 json 格式输出
   kubectl get pods nginx -o json

6. 高级输出 之 筛选
-------------------

筛选对象
~~~~~~~~

**使用 –field-selector**

.. code:: bash

   # 获取当前命名空间中正在运行的 Pods
   kubectl get pods --field-selector=status.phase=Running

**使用 –selector**

.. code:: bash

   # 获取所有工作节点（使用选择器以排除标签名称为 'node-role.kubernetes.io/master' 的结果）
   kubectl get node --selector='!node-role.kubernetes.io/master'

筛选字段
~~~~~~~~

**使用 jsonpath**

.. code:: bash

   # 获取全部节点的 ExternalIP 地址
   kubectl get nodes -o jsonpath='{.items[*].status.addresses[?(@.type=="ExternalIP")].address}'

**使用 json + jq**

.. code:: bash

   # 列出被一个 Pod 使用的全部 Secret
   kubectl get pods -o json | jq '.items[].spec.containers[].env[]?.valueFrom.secretKeyRef.name' | grep -v null | sort | uniq

**使用 custom-columns**

.. code:: bash

   # 集群中运行着的所有镜像
   kubectl get pods -A -o=custom-columns='DATA:spec.containers[*].image'

   # 除 "k8s.gcr.io/coredns:1.6.2" 之外的所有镜像
   kubectl get pods -A -o=custom-columns='DATA:spec.containers[?(@.image!="k8s.gcr.io/coredns:1.6.2")].image'

   # 输出 metadata 下面的所有字段，无论 Pod 名字为何
   kubectl get pods -A -o=custom-columns='DATA:metadata.*'

筛选对象+字段
~~~~~~~~~~~~~

.. code:: bash

   # 获取包含 app=cassandra 标签的所有 Pods 的 version 标签
   kubectl get pods \
     --selector=app=cassandra -o \
     jsonpath='{.items[*].metadata.labels.version}'

7. 高级输出 之 排序
-------------------

.. code:: bash 

   # 列出当前名字空间下所有 Services，按名称排序
   kubectl get services --sort-by=.metadata.name

   # 列出 Pods，按重启次数排序
   kubectl get pods --sort-by='.status.containerStatuses[0].restartCount'

   # 列举所有 PV 持久卷，按容量排序
   kubectl get pv --sort-by=.spec.capacity.storage


   # 列出事件（Events），按时间戳排序
   kubectl get events --sort-by=.metadata.creationTimestamp

8. 从标准输入创建对象
---------------------

有些对象的创建是临时的，不需要事先创建一个 yaml 再
apply，这时候就可以直接从标准输入创建对象

.. code:: bash

   # 从标准输入创建多个 YAML 对象
   cat <<EOF | kubectl apply -f -
   apiVersion: v1
   kind: Pod
   metadata:
     name: busybox-sleep
   spec:
     containers:
     - name: busybox
       image: busybox
       args:
       - sleep
       - "1000000"
   ---
   apiVersion: v1
   kind: Pod
   metadata:
     name: busybox-sleep-less
   spec:
     containers:
     - name: busybox
       image: busybox
       args:
       - sleep
       - "1000"
   EOF

9. 清单与集群对象差异
---------------------

.. code:: bash

   # 比较当前的集群状态和假定某清单被应用之后的集群状态
   kubectl diff -f ./my-manifest.yaml

10. 查看Pod 负载情况
--------------------

.. code:: bash

   # 显示给定 Pod 和其中容器的监控数据
   kubectl top pod POD_NAME --containers

   # 显示给定 Pod 的指标并且按照 'cpu' 或者 'memory' 排序
   kubectl top pod POD_NAME --sort-by=cpu              

11. 多种姿势查看日志
--------------------

.. code:: bash 

   # 获取 pod 日志（标准输出）
   kubectl logs my-pod            

   # 获取含 name=myLabel 标签的 Pods 的日志（标准输出）
   kubectl logs -l name=myLabel                

   # 获取上个容器实例的 pod 日志（标准输出）
   kubectl logs my-pod --previous                      

   # 获取 Pod 容器的日志（标准输出, 多容器场景）
   kubectl logs my-pod -c my-container                 

   # 获取含 name=myLabel 标签的 Pod 容器日志（标准输出, 多容器场景）
   kubectl logs -l name=myLabel -c my-container        

   # 获取 Pod 中某容器的上个实例的日志（标准输出, 多容器场景）
   kubectl logs my-pod -c my-container --previous      
   # 流式输出 Pod 的日志（标准输出）
   kubectl logs -f my-pod                             

   # 流式输出 Pod 容器的日志（标准输出, 多容器场景）
   kubectl logs -f my-pod -c my-container              

   # 流式输出含 name=myLabel 标签的 Pod 的所有日志（标准输出）
   kubectl logs -f -l name=myLabel --all-containers   

K8S 组件的日志等级非常多，共分 10 级，分别是

+-----------+---------------------------------------------------------+
| 详细程度  | 描述                                                    |
+===========+=========================================================+
| ``--v=0`` | 用于那些应该 *始终*                                     |
|           | 对运维人员可见的信息，因为这些信息一般很有用。          |
+-----------+---------------------------------------------------------+
| ``--v=1`` | 如                                                      |
|           | 果您不想要看到冗余信息，此值是一个合理的默认日志级别。  |
+-----------+---------------------------------------------------------+
| ``--v=2`` | 输出有关服务的                                          |
|           | 稳定状态的信息以及重要的日志消息，这些信息可能与系统中  |
|           | 的重大变化有关。这是建议大多数系统设置的默认日志级别。  |
+-----------+---------------------------------------------------------+
| ``--v=3`` | 包含有关系统状态变化的扩展信息。                        |
+-----------+---------------------------------------------------------+
| ``--v=4`` | 包含调试级别的冗余信息。                                |
+-----------+---------------------------------------------------------+
| ``--v=5`` | 跟踪级别的详细程度。                                    |
+-----------+---------------------------------------------------------+
| ``--v=6`` | 显示所请求的资源。                                      |
+-----------+---------------------------------------------------------+
| ``--v=7`` | 显示 HTTP 请求头。                                      |
+-----------+---------------------------------------------------------+
| ``--v=8`` | 显示 HTTP 请求内容。                                    |
+-----------+---------------------------------------------------------+
| ``--v=9`` | 显示 HTTP 请求内容而且不截断内容。                      |
+-----------+---------------------------------------------------------+

当你使用 kubectl logs 查看日志时，默认筛选等级为 1 的日志。

有时候排查问题的需要，需要更详细的日志来辅助定位，这时候可以加
``--v=x``\ ，其中 x 为日志等，可选值有 0～9

.. code:: bash

   kubectl logs --v=4 kube-scheduler-master -n kube-system

12. 连到到容器中
----------------

.. code:: bash

   # 在已有的 Pod 中运行命令（单容器场景）
   kubectl exec my-pod -- ls /                  

   # 使用交互 shell 访问正在运行的 Pod (一个容器场景)
   kubectl exec --stdin --tty my-pod -- /bin/sh        

   # 在已有的 Pod 中运行命令（多容器场景）
   kubectl exec my-pod -c my-container -- ls /         

参考文章
--------

-  `kubectl
   备忘单 <https://kubernetes.io/zh/docs/reference/kubectl/cheatsheet/>`__
-  `kubectl
   官方帮助文档 <https://kubernetes.io/zh/docs/reference/kubectl/>`__

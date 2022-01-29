2.2 从 Pause 容器理解 Pod 的本质
================================

在 K8S 中，Pod 是最核心、最基础的资源对象，它是 Kubernetes
中调度最小单元，学习 K8S 很多时候，我们都是在跟 Pod
打交道，它的内容是最多的，需要分好多的章节才能将它讲透。

本篇作为 Pod 的首篇，打算先从咱们熟悉的 Docker 容器入手，介绍 Pod
的组成及其工作原理。

主要解决几个关键问题：

1. Pod 是什么？它与容器是什么关系？
2. 为什么 K8S 不直接管理容器呢？

1. Pod 与 容器的关系
--------------------

都说 K8S 是容器编排引擎，那怎么 K8S 中最小的可管理可部署的计算单元是 Pod
而不是容器呢？

**Pod 和 容器，又是什么关系呢？**

其实 Pod
只是一个抽象的逻辑概念，它是一组（一个或者多个）容器的集合，这些容器之间共享同一份存储、网络等资源。

.. image:: http://image.iswbm.com/image-20220129125341713.png

使用 ``kubectl get po -o wide``\ 可以查看 pod 的列表，其中 READY
列代表该 Pod 总共有 1 个容器，并且该容器已经成功启动，可以对外提供服务了

.. image:: http://image.iswbm.com/image-20220127205612423.png

登陆到该 Pod 年在到 worker 节点上，使用 docker ps 查看容器

.. image:: http://image.iswbm.com/image-20220127205915339.png

咦？上面不是说该 Pod 只有一个容器吗？怎么这个 grep 出来，却有两个呢？

实际上，这个 pause 容器，是一个很特殊的容器，它又叫 infra 容器，是每个
Pod 都会自动创建的容器，它不属于用户自定义的容器。

**那么这个 pause 容器有什么用呢？**

接下来就来说说 pause 诞生的背景，它对 Pod 模型的理解有非常重要的意义。

2. Pause 容器
-------------

pause 容器镜像
~~~~~~~~~~~~~~

使用 ``docker insepct [CONTAAINER_ID]`` 查看一下 pause
容器的详情信息，可以发现 pause 容器使用的镜像为

::

   registry.cn-hangzhou.aliyuncs.com/google_containers/pause:3.6

该镜像非常小，只有 484KB，由于它总是处于 Pause （暂时）状态，所以取名叫
pause

想了解该 pause 容器的构成（代码是用 C
语言写的）的可以去官方仓库上一看究竟：https://github.com/kubernetes/kubernetes/tree/master/build/pause

pause 容器作用
~~~~~~~~~~~~~~

上面我们说，一个 Pod
是由一组容器组成的，这些容器之间共享存储和网络资源，那么网络资源是如何共享的呢？

假设现在有一个 Pod，它包含两个容器（A 和 B），K8S
是通过让他们加入（join）另一个第三方容器的 network namespace
实现的共享，而这个第三方容器就是 pause 容器。

.. figure:: http://image.iswbm.com/image-20220129125243265.png
   :alt: 2-2-2 Infra/Pause Container

   2-2-2 Infra/Pause Container

这么做的目的，其实很简单，想象一下，如果没有这样的第三方容器，会发生怎样的结果？

没有 pause 容器，那么 A 和 B 要共享网络，要不就是 A 加入 B 的 network
namespace，要嘛就是 B 加入 A 的 network namespace，
而无论是谁加入谁，只要 network 的 owner 退出了，该 Pod
里的所有其他容器网络都会立马异常，这显然是不合理的。

反过来，由于 pause
里只有是挂起一个容器，里面没有任何复杂的逻辑，只要不主动杀掉 Pod，pause
都会一直存活，这样一来就能保证在 Pod 运行期间同一 Pod
里的容器网络的稳定。

我们在同一 Pod
里所有容器里看到的网络视图，都是完全一样的，包括网络设备、IP 地址、Mac
地址等等，因为他们其实全是同一份，而这一份都来自于 Pod 第一次创建的这个
Infra container。

由于所有的业务容器都要依赖于 pause 容器，因此在 Pod
启动时，它总是创建的第一个容器，可以说 Pod 的生命周期就是 pause
容器的生命周期。

3. 手工模拟 Pod
---------------

从上面我们已经知道，一个 Pod
从表面上来看至少由一个容器组成，而实际上一个 Pod
至少要有包含两个容器，一个是业务容器，一个是 pause 容器。

理解了这个模型，我们就可以用以前熟悉的 docker
容器，手动创建一个真正意义上的 Pod。

.. figure:: http://image.iswbm.com/image-20220129132232935.png
   :alt: 2-2-3 Faker Pod via Docker

   2-2-3 Faker Pod via Docker

创建 pause 容器
~~~~~~~~~~~~~~~

使用 docker run 加如下参数：

-  ``--name``\ ：指定 pause 容器的名字，fake_k8s_pod_pause
-  ``-p 8888:80``\ ：将宿主机的 8888 端口映射到容器的 80 端口

.. code:: bash 

   sudo docker run -d -p 8888:80 \
           --ipc=shareable \
           --name fake_k8s_pod_pause \
           registry.cn-hangzhou.aliyuncs.com/google_containers/pause:3.6

创建 nginx 容器
~~~~~~~~~~~~~~~

创建容器之前先准备一下 nginx.conf 配置文件

::

   cat <<EOF >> nginx.conf
   error_log stderr;
   events { worker_connections  1024; }
   http {
       access_log /dev/stdout combined;
       server {
           listen 80 default_server;
           server_name iswbm.com www.iswbm.com;
           location / {
               proxy_pass http://127.0.0.1:2368;
           }
       }
   }
   EOF

然后运行如下命令创建名字 fake_k8s_pod_nginx 的 nginx 容器

.. code:: bash

   sudo docker run -d --name fake_k8s_pod_nginx \
           -v `pwd`/nginx.conf:/etc/nginx/nginx.conf \
           --net=container:fake_k8s_pod_pause \
           --ipc=container:fake_k8s_pod_pause \
           --pid=container:fake_k8s_pod_pause \
           nginx

其中 -v 参数是将宿主机上的 nginx.conf 文件挂载给 nginx 容器

除此之外，还有另外三个核心参数：

-  ``--net``\ ：指定 nginx 要 join 谁的 network
   namespace，当然是前面创建的fake_k8s_pod_pause
-  ``--ipc``\ ：指定 ipc mode， 一样指定前面创建的fake_k8s_pod_pause
-  ``--pid``\ ：指定 nginx 要 join 谁的 pid
   namespace，照旧是前面创建的fake_k8s_pod_pause

创建 ghost 容器
~~~~~~~~~~~~~~~

有了 nginx 还不够，还需要有人提供网页的数据，这里使用 ghost
这个博客应用，参数和上面差不多，这里不再赘述。

.. code:: bash

   sudo docker run -d --name ghost \
           --net=container:fake_k8s_pod_pause \
           --ipc=container:fake_k8s_pod_pause \
           --pid=container:fake_k8s_pod_pause 
           ghost

到这里，我就纯手工模拟出了一个符合 K8S Pod 模型的 “Pod” ，只是它并不由
K8S 进行管理。

这个 “Pod” 由一个 fake_k8s_pod_pause
容器（负责提供可稳定共享的命名空间）和两个共享 fake_k8s_pod_pause
容器命名空间的两业务容器。

访问 “Pod” 服务
~~~~~~~~~~~~~~~

由于我是在 worker （ip 为 172.20.20.11）节点上创建的 “Pod”，因此在我的
Mac 电脑上，直接访问 ``http://172.20.20.11:8888/`` 就可以访问该博客啦

.. image:: http://image.iswbm.com/image-20220127223816227.png

4. 创建真正的 Pod
-----------------

上一节，我在 K8S 生态之外，单纯使用 Docker
创建了三个容器（Pause、Nginx、Ghost），这三个容器的的组合，在 K8S
中称之为 Pod。

.. figure:: http://image.iswbm.com/image-20220129203749070.png
   :alt: 2-2-4 Faker Pod via Docker

   2-2-4 Faker Pod via Docker

如果没有 K8S 的 Pod ，你启动一个 ghost
博客服务，你需要手动创建三个容器，当你想销毁这个服务时，同样需要删除三个容器。

而有了 K8S 的 Pod，这三个容器在逻辑上就是一个整体，创建 Pod
就会自动创建三个容器，删除 Pod
就会删除三个容器，从管理上来讲，方便了不少。

这正是 Pod 存在的一个根本意义所在。

那到底有多方便呢？还是以上面 ghost 博客为例，下面我会介绍如何 K8S
中创建一个像上面一样的博客应用？

创建 ConfigMap
~~~~~~~~~~~~~~

ConfigMap 也是 K8S
中的一个对象，目前还没有学到，你只要知道它是一个用来存储信息的对象即可

使用如下命令即可创建一个 ConfigMap 对象，用它来存储 nginx.conf 文件。

.. code:: bash

   kubectl create configmap nginx-config --from-file=nginx.conf

使用 ``-o yaml`` 参数，就能看到 nginx.conf 文件中的内容。

.. image:: http://image.iswbm.com/image-20220127231810029.png

创建 Pod
~~~~~~~~

接着执行如下命令创建一个 ghost.yaml 文件

.. code:: bash

   cat <<EOF >> ghost.yaml
   apiVersion: v1
   kind: Pod
   metadata:
     name: ghost
     namespace: default
   spec:
     containers:
     - image: nginx
       imagePullPolicy: IfNotPresent
       name: nginx
       ports:
       - containerPort: 80
         protocol: TCP
         hostPort: 8888
         volumeMounts:
       - mountPath: /etc/nginx/
         name: nginx-config
         readOnly: true
     - image: ghost
       name: ghost
       volumes:
      - name: nginx-config
        configMap:
          name: nginx-config
        EOF

然后直接 apply 该文件就可以创建一个 ghost 服务，从输出可以看到这里的
READY 变成了 ``2/2``\ ，意思是该 Pod 总共包含 2
个容器，目前已经全部准备就绪。

.. image:: http://image.iswbm.com/image-20220127232134367.png

此时再去访问 ``http://172.20.20.11:8888/`` 一样可以访问博客页面

.. image:: http://image.iswbm.com/image-20220127223816227.png

5. 总结一下
-----------

本文以 pause 容器为突破口，在脱离 K8S 生态之下，使用 docker
手工创建具有业务相关的多个容器，模拟出最初的 Pod
模型，理解了这个基本就对 Pod 的意义有了一个直观、深刻的认识。

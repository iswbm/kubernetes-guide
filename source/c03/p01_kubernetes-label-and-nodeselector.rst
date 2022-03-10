3.1 调度利器（一）：标签与选择器
================================

将一个 Pod 分配到某一个可以满足 Pod
资源请求的节点上，这一过程称之为调度。

理想情况下，你的集群中，有足够的资源能让你创建你期望的
Pod，如此一来，你就有理由不关心你的节点的资源还剩多少，有理由不关心 K8S
调度 Pod 的细节。

可事实上，你的集群资源是有限的，为了能让节点资源得到合理分配、有效利用，需要你对节点进行规划。

比如哪些机器是高性能的机器，哪些是普通机器，哪些是专用机器，尽量避免让普通的应用跑在高性能的机器上。

除此之外，有些应用，出于高可用的考虑，还需要应用部署多个副本，并分散开在不同的域里。

而关于这些内容，可以分成三个部分：

-  标签与选择器
-  污点与容忍度
-  亲和与反亲和

本篇文章先介绍 **标签与选择器**\ 。

1. 通俗理解标签
---------------

打个比方，在你面前的食物摆放着一堆食物，分类起来，可以分为两种：

1. **零食**\ ：薯片、辣条 等
2. **水果**\ ：苹果、香蕉 等

肚子饿的时候，你的头脑，首先给出信号：好饿，我想吃零食。

于是你吃的东西，就被限定在了【零食】分组里，而不会去吃水果分组里的东西。

这即是分组的作用，在本例中：

-  薯片、辣条、苹果、香蕉等食物，即为 K8S 中的 Node
-  零食、水果，则是打在食物（K8S 中 Node） 上的标签
-  而大脑给出的进食信号，而是 K8S 中的 Pod

可以看出，标签实际上是从 Pod 的角度，约束了 Pod
只能调度到那些满足条件的节点上。

2. 如何打标签？
---------------

标签是打在 Node 上，可以理解为 Node 的属性，或者说你为 Node 分的组名。

使用如下两条命令分别为 worker01 和 worker02 打上 disktype 的分组标签

.. code:: bash

    kubectl label node worker01 disktype=ssd
    kubectl label node worker02 disktype=hdd

3. 选择器的作用
---------------

在 Pod 的 spec 中可以指定一个 nodeSelector 对象，它是一个 map
字典，字典里的每个 key-value ，分别对应 node 上的 label。

当我在 nodeSelector 里指定了 disktype: ssd 后

.. image:: https://image.iswbm.com/20220308204936.png

就意味着，该 Pod 只能调度到 worker01 上，而不能调度到 worker02 上。

当然，如果 nodeSelector
指定了多个标签，那么指定的标签都需要满足，才能调度成功。

.. image:: https://image.iswbm.com/20220308225238.png

4. 标签的操作
-------------

与标签有关的命令，这边也一并说下。

删除某个标签
~~~~~~~~~~~~

如果想要删除原有标签，可以使用

.. code:: bash

    kubectl label node worker01 disktype-
    kubectl label node worker02 disktype-

显示所有标签
~~~~~~~~~~~~

如果想查看某种资源对象的所有标签可以加 ``--show-labels``

.. code:: bash

   [root@master01 ~]# kubectl get pods --show-labels
   NAME                               READY   STATUS    RESTARTS   AGE    LABELS
   nginx-test                         1/1     Running   0          5d8h   app=nginx

根据标签过滤
~~~~~~~~~~~~

当我们使用 kubectl get pods 时，会列出当前 namespace 的所有
pod，若只想显示有某个 label 的 pod 呢？可以使用 ``-l``
命令指定标签，比较符可以是 ``=`` 和 ``!=``

.. code:: bash

   [root@master01 ~]# kubectl get pods -l app=nginx
   NAME         READY   STATUS    RESTARTS   AGE
   nginx-test   1/1     Running   0          5d8h

除此之外，也使用 in 和 notin 来判断标签的集合关系

.. code:: bash

   [root@master01 ~]# kubectl get pod -l "app in (web,nginx)" --show-labels
   NAME         READY   STATUS    RESTARTS   AGE    LABELS
   nginx-test   1/1     Running   0          5d8h   app=nginx,env=test
   [root@master01 ~]#
   [root@master01 ~]# kubectl get pod -l "env notin (product,dev)" --show-labels
   NAME                               READY   STATUS    RESTARTS   AGE    LABELS
   nginx-test                         1/1     Running   0          5d8h   app=nginx,env=test

更简单一点，直接判断存在某个标签或者不存在某个标签，注意在判断不存在某个标签时，需要使用单引号包裹

.. code:: bash

   [root@master01 ~]# kubectl get pod -l app
   NAME         READY   STATUS    RESTARTS   AGE
   nginx-test   1/1     Running   0          5d8h
   [root@master01 ~]#
   [root@master01 ~]#
   [root@master01 ~]# kubectl get pod -l '!dev'
   NAME                               READY   STATUS    RESTARTS   AGE
   nginx-test                         1/1     Running   0          5d8h

显示某些标签
~~~~~~~~~~~~

当标签较多时，也可以使用 ``-L`` 来指定显示那些标签；

.. code:: bash

   [root@master01 ~]# kubectl get pods -L app
   NAME                               READY   STATUS    RESTARTS   AGE    APP
   nginx-test                         1/1     Running   0          5d8h   nginx

修改某个标签
~~~~~~~~~~~~

.. code:: bash

   [root@master01 ~]# kubectl label pod nginx-test app=web --overwrite
   pod/nginx-test labeled
   [root@master01 ~]#
   [root@master01 ~]# kubectl get pods -L app
   NAME                               READY   STATUS    RESTARTS   AGE    APP
   nginx-test                         1/1     Running   0          5d8h   web

添加多个标签
~~~~~~~~~~~~

直接在后面添加多个 key=value 即可

.. code:: bash

   [root@master01 ~]# kubectl label pod nginx-test app=nginx env=test
   pod/nginx-test labeled
   [root@master01 ~]#
   [root@master01 ~]# kubectl get pod --show-labels
   NAME                               READY   STATUS    RESTARTS   AGE    LABELS
   nginx-test                         1/1     Running   0          5d8h   app=nginx,env=test

5. 语法与字符集
---------------

标签的 key 和 value，是有长度限制的，都不能超过63个字符。

并且标签必须以字母数字字符（\ ``[a-z0-9A-Z]``\ ）开头和结尾，
中间的字符可以用破折号（\ ``-``\ ），下划线（\ ``_``\ ），点（ ``.``\ ）

举个反例，如下 key 是不合法的，因为它没有用 [a-z0-9A-Z] 开头

.. code:: bash

   __disk_type

如果你的标签有域名或者前缀，可以用 ``/`` 来分隔，比如

.. code:: bash

   ovn.kubernetes.io/pod_nic_type: veth-pair
   ovn.kubernetes.io/routed: "true"

你可以随意定义，但 K8S 有两个保留前缀你无法使用，

-  ``kubernetes.io/``
-  ``k8s.io/``

6. 总结一下
-----------

K8S 中的标签用来给资源对象分类，任何已注册到 K8S
中的资源对象（标签并不是 Node 和 Pod 的专属），你都可以使用 kubectl
label 去操作标签。

而对于 Pod 和 Node 来说，标签还有一层作用，就是借助 nodeSelector
实现指定节点的属性来辅助调度。

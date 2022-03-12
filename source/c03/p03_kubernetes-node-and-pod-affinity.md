# 3.3 调度利器（三）：亲和与反亲和（服务容灾）

将一个 Pod 分配到某一个可以满足 Pod 资源请求的节点上，这一过程称之为调度。

理想情况下，你的集群中，有足够的资源能让你创建你期望的 Pod，如此一来，你就有理由不关心你的节点的资源还剩多少，有理由不关心 K8S 调度 Pod 的细节。

可事实上，你的集群资源是有限的，为了能让节点资源得到合理分配、有效利用，需要你对节点进行规划。

比如哪些机器是高性能的机器，哪些是普通机器，哪些是专用机器，尽量避免让普通的应用跑在高性能的机器上。

除此之外，有些应用，出于高可用的考虑，还需要应用部署多个副本，并分散开在不同的域里。

而关于这些内容，可以分成三个部分：

* 标签与选择器
* 污点与容忍度
* 亲和与反亲和

前面两篇文章已经介绍了 **标签与选择器** 与 **污点与容忍度**，本篇文章讲一下 **亲和与反亲和**。

## 1. 通俗理解亲和性

按照惯例，解释一个新名词前，我会拿生活中的例子做类比，方便大家轻松上手。

公司组织员工出去团建，带头人策划了一个小游戏，这个小游戏会将成员分成几个不同的小组进行 PK，最终以团队的比分做为排名依据。

员工可以自由选择队友，这时候就有两种选择的标准：

* 第一种：我有社交恐惧症，只选自己熟悉的同事，自己容易融入。这种就是亲和性原则
* 第二种：我有社交牛逼症，只选自己陌生的同事，能交到新朋友。这种就是反亲和原则

这里的员工就是 K8S 中的 Pod，而“熟悉” 和 “陌生” 就是 Pod 上的标签。

> 要注意的是在这里有一点点不一样，因为对于每个人来说这里的标签值是不一样的，而在 Pod 上标签是固定值
>

## 2. 亲和性调度与 nodeSelector 

 以你目前的知识储备来看，应该会认为上面的亲和性做法，和之前学习过的 nodeSelector 很像吧？

仅以上面的例子来看，确实亲和性做法，就是 nodeSelector。

但实际上亲和性调度，远比 nodeSelector 强大许多，还是以上面的亲和性做法来举例

若以 nodeSelector 来实现上面的亲和性原则来组队，那 nodeSelector 就是脑子一根筋，只选自己熟悉的同事，不熟悉的，一概不选。

这么一来，就有可能，所有你熟悉的同事已经被别人捷足先登抢先拉拢了，而最后只剩你一个人孤零零的。

换成亲和性调度，就变得灵活许多，他可以设置两种策略：

对于亲和性和反亲和性，都可以设置：

* preferredDuringSchedulingIgnoredDuringExecution  ==> 软策略
* requiredDuringSchedulingIgnoredDuringExecution ==> 硬策略

硬策略的做法，就是换个模式的 nodeSelector，它是强制性的，不满足就调度失败。

软策略的做法，则更灵活，可以选择满足条件的，要是真没有满足条件的，就调度到其他节点上（选择自己陌生的同事）

## 3. 亲和性的三个种类

对比 nodeSelector 来说，亲和性调度除非了上面可以选择软策略之外，还有更多强大的功能。

亲和性调度器定义在 `.spec.affinity` 字段里，通过 explain 命令可以查看其字段

```yaml
KIND:     Pod
VERSION:  v1

RESOURCE: affinity <Object>

DESCRIPTION:
     If specified, the pod's scheduling constraints

     Affinity is a group of affinity scheduling rules.

FIELDS:
   nodeAffinity	<Object>
     Describes node affinity scheduling rules for the pod.

   podAffinity	<Object>
     Describes pod affinity scheduling rules (e.g. co-locate this pod in the
     same node, zone, etc. as some other pod(s)).

   podAntiAffinity	<Object>
     Describes pod anti-affinity scheduling rules (e.g. avoid putting this pod
     in the same node, zone, etc. as some other pod(s)).
```

可以看到亲和性调度器，有如下三种：

* nodeAffinity(node 亲和性)：该 Pod 喜欢调度到什么样的 Node 上
* podAffinity(pod 亲和性) ：该 Pod 喜欢和某些 Pod 调度在一起
* podAntiAffinity(pod 反亲和性)：该 Pod 不喜欢和某些 Pod 调度在一起

上面三种亲和性调度，无论是哪一种，都要依赖标签才能起作用，只是不同的亲和性调度方法，亲和性调度器匹配标签的对象不同

* node 亲和性：检查的是亲和性调度器与 node 标签的匹配
* pod (反)亲和性：检查的是亲和性调度器与 pod 标签的匹配


## 4. 亲和性调度示例

### 4.1 node 亲和性 + 硬策略

如下是一个使用 node 亲和性调度器的简单示例，并且使用的是硬策略。

该段配置的意思是，当 kube-scheduler 在判断一个节点是否能通过筛选时，会先取出 node 上的 kubernetes.io/hostname 标签，当该标签的值为 worker01 时，则不允许调度。

一句话总结，就是不允许调度到 worker01 上

```yaml
      affinity:
        nodeAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:  # 硬策略
            nodeSelectorTerms:
            - matchExpressions:
              - key: kubernetes.io/hostname
                operator: NotIn
                values:
                - worker01
```


### 4.2 node 亲和性 + 软策略

如下是一个使用 node 亲和性调度器的简单示例，并且使用的是软策略。

该段配置的意思是，当 kube-scheduler 在判断一个节点是否能通过筛选时，会先取出 node 上的 disktype 标签，当该标签的值为 ssd 时， 该节点的权重 +100，反之标签值不为 ssd，则节点的权重值 +0

一句话总结，就是尽量 调度到有 ssd 的节点上。

```yaml
      affinity:
        nodeAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:  # 软策略
          - weight: 100
            preference:
              matchExpressions:
              - key:  disktype
                operator: In
                values:
                - ssd
```

### 4.3 Pod 亲和性 + 硬策略

假设你在集群中部署有两个服务，分别为 S1 和 S2，其中 S1 使用 S2 的服务。

为了减少他们之间的网络延迟（或其他原因），会考虑将 S1 和 S2 的Pod 部署在同一拓扑域中

这就是依赖 Pod 的亲和性实现的

如下是一个简单的示例

```yaml
      affinity:
        podAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:  # 硬策略
            labelSelector:
              matchExpressions:
              - key: security
                operator: In
                values:
                - S1
          topologyKey: "kubernetes.io/hostname"
```

在这个示例中，它要求该 Pod 要调度与有标签键为 security 且值为 S1 的 Pod 同一个域上，其中域的 key 为 kubernetes.io/hostname，则域的范围就是节点级。

### 4.4 Pod 亲和性 + 软策略

还是以 4.3 的例子来说明，若想让 S1 和 S2 尽量调度到一起，当集群资源不那么充裕时，不调在一起也可以时，就要使用软策略。

具体配置如下

```yaml
      affinity:
        podAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:  # 软策略
          - weight: 100
            podAffinityTerm:
              labelSelector:
                matchExpressions:
                - key:  security
                  operator: In
                  values:
                  - S1
              topologyKey: "kubernetes.io/hostname"
```

### 4.5 Pod 反亲和 + 硬策略

当使用 Deployment 创建多副本的 Pod 时，这些多副本是有可能创建到同一个域（或节点）上的。

若多个副本创建到同一个域（或节点）上，当该域（或节点）发生故障，就会有多个副本无法工作，原来的副本就失去了意义。

因此，我们希望能让副本能打散调度到不同的域（或节点）上，这就要用到反亲和调度器。

如下是一个反亲和调度器的简单示例，在这个示例中，Deployment 创建了三副本的 Pod，而这些 Pod 不能创建在同一个域（本示例上，域为节点）上

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis-cache
spec:
  selector:
    matchLabels:
      app: store
  replicas: 3
  template:
    metadata:
      labels:
        app: store
    spec:
      affinity:
        podAntiAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
          - labelSelector:
              matchExpressions:
              - key: app
                operator: In
                values:
                - store
            topologyKey: "kubernetes.io/hostname"
      containers:
      - name: redis-server
        image: redis:3.2-alpine
```

### 4.6 Pod 反亲和 + 软策略

还是以 4.5 的例子来说明，当集群资源不那么充裕时，不打散也能接受的话，就要使用软策略。

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis-cache
spec:
  selector:
    matchLabels:
      app: store
  replicas: 3
  template:
    metadata:
      labels:
        app: store
    spec:
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:  # 软策略
          - weight: 100
            podAffinityTerm:
              labelSelector:
                matchExpressions:
                - key:  app
                  operator: In
                  values:
                  - store
              topologyKey: "kubernetes.io/hostname"
      containers:
      - name: redis-server
        image: redis:3.2-alpine
```

## 5. 域和匹配方式

在上面的诸多示例中，为了方便：

* 域都是使用的是 `kubernetes.io/hostname`
* 并且都是使用的 `matchExpressions`

关于第一个问题，实际上K8S 有内置三种域的 key，分别是 `kubernetes.io/hostname`和 `topology.kubernetes.io/region` 和 `topology.kubernetes.io/zone`，最常用的就是 `kubernetes.io/hostname` ，大家可根据自身需求进行选择。

关于第二个问题，上面使用 matchExpressions 是更通用、更灵活的方式，因为 matchExpressions 可以利用操作符（operator）做更多复杂的判断

下面是操作的可选项及其含义：

* In：label 的值在某个列表中
* NotIn：label 的值不在某个列表中
* Gt：label 的值大于某个值
* Lt：label 的值小于某个值
* Exists：某个 label 存在
* DoesNotExist：某个 label 不存在

不同调度器支持的操作符不太一样，可参考下面表格

若只是单纯的 security=S1，可以直接使用 matchLabels ，书写更加快捷，也更容易理解

因此下面两种方法在效果上是等价的

```yaml
# 第一种写法：使用 matchExpressions
      affinity:
        podAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:  # 硬策略
            labelSelector:
              matchExpressions:
              - key: security
                operator: In
                values:
                - S1
          topologyKey: "kubernetes.io/hostname"

# 第二种写法：使用 matchLabels
      affinity:
        podAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:  # 硬策略
            labelSelector:
              matchLabels:
                security: S1
          topologyKey: "kubernetes.io/hostname"
```



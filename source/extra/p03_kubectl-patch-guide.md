# 3. 详解 kubectl patch 命令 -- strategic、json 和 merge 区别

## 1. 命令的组成

patch 命令可以分成以下几个部分

**第一、指定要更新的对象**

有两种方式，可以用 -f 后加一个 json 或者 yaml 文件（目前没有看到例子），也可直接使用 type NAME （比如 pod test-pod）

**第二、指定要更新成啥样**

有两种方式，可以用 -p 'xxxx'，其中 xxx 为json 或 yaml 文本，也可直接将文本写入文件中，再用 --patch-file xxx.yaml 传入

```bash
# 现在两种方法等价
kubectl patch deployment patch-demo --patch "$(cat patch-file-containers.yaml)"
kubectl patch deployment patch-demo --patch-file patch-file-containers.yaml
```

**第三、额外的非必要参数**

这些参数比较多，后面统一介绍

```
kubectl patch \
        (-f FILENAME | TYPE NAME) \
        [-p PATCH|--patch-file FILE] \
        [options]
```

## 2. option 选项

使用 help 命令可以查看 option 的选项，我挑几个比较高频的选项进行讲解，其他的我暂时没有使用过，后续再研究

```bash
```

### 2.1 --dry-run

--dry-run，只会尝试 patch，检查一些格式的检查，并不会真正地提交到 api-server 上，它的值有三种情况：

* none：默认值，也即不使用 dry-run
* client：只在客户端打印更新完要更新的对象
* server：会把要更新的对象请求发到服务端，但不持久化更新

```
kc patch kubevirt kubevirt -n kubevirt \
        -p '[{"op": "replace", "path": "/spec/configuration/developerConfiguration/useEmulation", "value": false}]' \
        --dry-run=client \
        --type=json
```

如果要查看 patch 后 dry-run 的配置，可以再加个 `--output=yaml`

在 client 和 server 的结果，有时候还是不一样的，建议使用 server，与最终的结果最为接近。

## 3. 重点与难点：--type

--type ，是 patch 的重点，也是难点。

我花费了很多力量，才大抵摸清了它们的区别和适用场景。

--type 有有四种情况：

### 第一种：strategic

全名是 strategic merge patch，翻译过来是策略合并，是默认的选项。

当你不指定 --type 或者  指定为 strategic，api-server 会根据 k8s crd 资源对象的字段定义（patchStrategy）决定如何该如何更新：

* 不指定 patchStrategy 时，策略即为 replace
* 除此之外，还可以配置策略为 merge

```go
type PodSpec struct {
  ...
  Containers []Container `json:"containers" patchStrategy:"merge" patchMergeKey:"name" ...`
```

或者也可以在[OpenApi spec](https://raw.githubusercontent.com/kubernetes/kubernetes/master/api/openapi-spec/swagger.json) 规范和  [Kubernetes API 文档](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.23/#podspec-v1-core)  看到 patch 策略：

```json
"io.k8s.api.core.v1.PodSpec": {
    ...
     "containers": {
      "description": "List of containers belonging to the pod. ...
      },
      "x-kubernetes-patch-merge-key": "name",
      "x-kubernetes-patch-strategy": "merge"
     },

```

那么 replace 和 merge 有什么区别呢？

假设有如下一段 json

```json
{
	"profile": {
		"name": "iswbm",
		"age": 28,
		"gender": "male",
	}
}
```

而我 patch 的 body 为

```json
{
	"profile": {
		"name": "iswbm",
		"age": 30,
	}
}
```

使用 replace 策略，则 patch 后 json 的值为

```json
{
	"profile": {
		"name": "iswbm",
		"age": 30,
	}
}
```

而使用 merge 策略，则 patch 后 json 的值如下，有变更的字段发生进行更新，没有变化的字段则进行合并，并不会删除。

```json
{
	"profile": {
		"name": "iswbm",
		"age": 30,
		"gender": "male",
	}
}

```

### 第二种：json

全名 json patch，`--type='json'` 的 --patch 参数，跟的应当是一个 json 列表，该列表里的每个对象，都应是如下结构

```json
[
    {
        "op" : "",
        "path" : "" ,
        "value" : ""
    }
]
```

如下是 help 的一个例子

```bash
 kubectl patch pod valid-pod --type='json' --patch='[{"op": "replace", "path": "/spec/containers/0/image", "value":"newimage"}]'
```

 **不管 crd 字段有没有加 patchStrategy ，对于 --type="json"，其实都不影响，因为它操作的是具体字段，并且清楚地指明是 remove,  add,  replace 操作**

### 第三种：merge

全名 json merge patch，有相同的字段就替换，没有相同的字段就合并。

**和前面在 crd 资源对象的字段定义（patchStrategy="merge"）效果一样，--type='merge' 应该是解决那些原来字段并没有指定 patchStrategy="merge"，但你又想使用 merge 策略的场景。**

`--type='json' ` 由于工作原理的特殊性，必须得使用 json 专有的格式来做为 --patch 的参数

而 `--type='merge'` 就比较随意了，格式就比较随意了

它可以是 yaml 格式

```
spec:
  template:
    spec:
      tolerations:
      - effect: NoSchedule
        key: disktype
        value: "ssd"
```

然后使用如下命令导入 patch

```bash
kubectl patch pod patch-demo --patch-file patch-file-tolerations.yaml --type="merge"
```

也可以是 json 格式

```
{
  "spec": {
    "template": {
      "spec": {
        "tolerations": [
          {
            "effect": "NoSchedule",
            "key": "disktype",
            "value": "ssd"
          }
        ]
      }
    }
  }
}
```

再使用 如下命令导入 patch

```bash
kubectl patch pod patch-demo --patch-file patch-file-tolerations.json --type="merge"

# 或者
kubectl patch pod patch-demo --patch '{"spec":{"template":{"spec":{"tolerations":[{"effect":"NoSchedule","key":"disktype","value":"ssd"}]}}}}' --type="merge"
```

对于 crd 字段有加 patchStrategy=merge 的，--type="merge" 加和不加都是一样的

比如 pod 的 containers 在 crd 定义里就指定了 patchStrategy=merge，因为如下两条命令完全等价

```
kubectl patch pod patch-demo -p '{"spec":{"containers":[{"name":"nginx","imagePullPolicy":"Always"}]}}'
kubectl patch pod patch-demo -p '{"spec":{"containers":[{"name":"nginx","imagePullPolicy":"Always"}]}}' --type="merge"
```

### 第四种：apply

其实 kubectl patch 命令仅有上面三种 patchType，apply 也是我在写某控制器时，偶尔发现的，应该只有使用 client-go 接口才能使用。

我大胆猜测， 当我们对一个对象 apply 一个 yaml 文件的操作，内部有可能就是执行的 patch。

```go
const (
        JSONPatchType           PatchType = "application/json-patch+json"
        MergePatchType          PatchType = "application/merge-patch+json"
        StrategicMergePatchType PatchType = "application/strategic-merge-patch+json"
        ApplyPatchType          PatchType = "application/apply-patch+yaml"
)
```

## 4. merge 的“坑”

### 第一个坑

如果一个字段的值为数组，则 `--type="merge"` 则是无效的，无论你有没有指定 `--type="merge"`，新的元素都将覆盖掉原先所有的列表元素。

希望你理解 `--type="merge"` 的意义和用途，它是为了让我们在 patch 时，可以指定一个 object 对象的更新的部分字段，而不用指定全量的字段。

若你操作的是列表，建议使用 `--type="json"` 操作，更加精准可控。

### 第二个坑

merge 想要删除一个 key，只能通过将 key 设置为 null，但有些 key 对应的 value 是不能为 null 的

## 5. json patch 转义字符

在 patch 的时候，有一些 key 比较特殊，会包含波浪线和斜杠，当 `--patch` 参数是 json 格式时，path 里的斜杠就会与 key 冲突，此时可以将 波浪线和斜杠 替换成如下转义字符

*  `～` （波浪线）对应的是`~0`
* `/` （斜杠）对应的是：`～1`

## 6. 参考文档

* https://kubernetes.io/zh/docs/tasks/manage-kubernetes-objects/update-api-object-kubectl-patch/
* https://erosb.github.io/post/json-patch-vs-merge-patch/
* https://cvvz.github.io/post/k8s-kubectl-patch/



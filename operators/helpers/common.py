from kubeconfig import KubeConfig

def switch_config(clusterName):
    # The context in kinD: kind- + (cluster)
    context = "kind-" + clusterName
    conf = KubeConfig()
    conf.use_context(context)
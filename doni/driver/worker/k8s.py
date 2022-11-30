import yaml
import json

from typing import TYPE_CHECKING

from kubernetes import config, client
from oslo_config.cfg import StrOpt, DictOpt
from oslo_log import log

LOG = log.getLogger(__name__)

from doni.conf import CONF
from doni.driver.worker.base import BaseWorker
from doni.worker import WorkerResult

if TYPE_CHECKING:
    from doni.common.context import RequestContext
    from doni.objects.availability_window import AvailabilityWindow
    from doni.objects.hardware import Hardware

# Kubernetes 10.x/12.x support
try:
    K8sApiException = client.ApiException  # >=12.x
except:
    K8sApiException = client.api_client.ApiException

_KUBERNETES_CLIENT = None


def kubernetes_client():
    global _KUBERNETES_CLIENT
    if not _KUBERNETES_CLIENT:
        config.load_kube_config(config_file=CONF.k8s.kubeconfig_file)
        _KUBERNETES_CLIENT = client.CoreV1Api()
    return _KUBERNETES_CLIENT


class K8sWorker(BaseWorker):
    opts = [
        StrOpt("kubeconfig_file", help="Kubeconfig file to use for calls to k8s"),
        StrOpt(
            "expected_labels_index_property",
            default="machine_name",
            help=(
                "The property name to use to index into the ``expected_labels`` "
                "configuration."
            ),
        ),
        DictOpt(
            "expected_labels",
            help=(
                "A mapping of the hardware property index key to a set of labels that "
                "should exist for k8s nodes associated w/ the hardware."
            ),
        ),
    ]
    opt_group = "k8s"

    def process(
        self,
        context: "RequestContext",
        hardware: "Hardware",
        availability_windows: "list[AvailabilityWindow]" = None,
        state_details: "dict" = None,
    ) -> "WorkerResult.Base":
        core_v1 = kubernetes_client()

        if hardware.deleted:
            self._delete_node(hardware)
            return WorkerResult.Success()

        idx_property = CONF.k8s.expected_labels_index_property
        idx = hardware.properties.get(idx_property)
        if not idx:
            raise ValueError(f"Missing {idx_property} on hardware {hardware.uuid}")

        expected_labels = CONF.k8s.expected_labels.get(idx)
        labels = {}
        # Expand config structure from "key1=value1,key2=value2" to dict
        for label_spec in expected_labels.split("|") if expected_labels else []:
            label, value = label_spec.split("=")
            labels[label] = value

        payload = {}
        if labels:
            try:
                core_v1.patch_node(hardware.name, {"metadata": {"labels": labels}})
            except K8sApiException as exc:
                if exc.status == 404:
                    return WorkerResult.Defer(reason="No matching k8s node found")
                else:
                    raise
            payload["num_labels"] = len(labels)
        else:
            payload["num_labels"] = 0


        # Add network-attachment-definitions
        # baremetal interfaces
        bm_interfaces = hardware.properties.get("bm_interfaces")
        if bm_interfaces:
            for interface in bm_interfaces:
                lli_list = interface["local_link_information"]
                lli_json = json.dumps(lli_list)
                dict_body = {
                    'apiVersion':'k8s.cni.cncf.io/v1',
                    'kind':'NetworkAttachmentDefinition',
                    'metadata':{
                        'name':"{0}.{1}".format(hardware.name,interface["name"]),
                    },
                    'spec': {
                        'config': ' '.join('{{\
                            \"cniVersion\": \"0.3.1\",\
                            \"local_link_information\":{0},\
                            \"plugins\": [{{\
                                \"type\": \"macvlan\",\
                                \"master\": \"{1}\",\
                                \"mode\": \"bridge\",\
                                \"ipam\": {{}}\
                            }},{{\
                                \"capabilities\":{{ \"mac\": true}},\
                                \"type\": \"tuning\"\
                            }}]\
                        }}'.format(lli_json,interface["name"]).split())
                    },
                }
                json_body = json.dumps(dict_body)
                try:
                    res = client.CustomObjectsApi().create_namespaced_custom_object(
                        group="k8s.cni.cncf.io",
                        version="v1",
                        plural="network-attachment-definitions",
                        namespace='default',
                        body=yaml.load(json_body,Loader=yaml.FullLoader),
                    )
                except Exception as e:
                    LOG.error(e)
                    return WorkerResult.Defer(reason="k8s create bm_interface network-attachment-definition did not work")

        return WorkerResult.Success(payload)

    def _delete_node(self, hardware: "Hardware"):
        LOG.info(f"delete k8s {hardware.name} network attachment definitions")
        # Remove network-attachment-definitions
        # baremetal interfaces
        bm_interfaces = hardware.properties.get("bm_interfaces")
        if bm_interfaces:
            for interface in bm_interfaces:
                LOG.info(f'delete network attachment definition: {interface["name"]}')
                try:
                    client.CustomObjectsApi().delete_namespaced_custom_object(
                        group="k8s.cni.cncf.io",
                        version="v1",
                        plural="network-attachment-definitions",
                        namespace='default',
                        name="{0}.{1}".format(hardware.name,interface["name"]),
                    )
                except Exception as e:
                    LOG.error(e)
                    return WorkerResult.Defer(reason="k8s delete br_interface network-attachment-definition did not work")


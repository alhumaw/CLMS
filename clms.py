r""" 

███████ ██     ██ ██    ██      ██████ ██    ██ ██████  ███████ ██████  
██      ██     ██ ██    ██     ██       ██  ██  ██   ██ ██      ██   ██ 
█████   ██  █  ██ ██    ██     ██        ████   ██████  █████   ██████  
██      ██ ███ ██ ██    ██     ██         ██    ██   ██ ██      ██   ██ 
███████  ███ ███   ██████       ██████    ██    ██████  ███████ ██   ██ 
                                                                        
                                                                        
                                         Eastern Washington University




   ____ _    _   _ ____ _____ _____ ____                           
  / ___| |  | | | / ___|_   _| ____|  _ \                          
 | |   | |  | | | \___ \ | | |  _| | |_) |                         
 | |___| |__| |_| |___) || | | |___|  _ <                          
  \____|_____\___/|____/ |_| |_____|_| \_\                         
  _     ___ _____ _____ ______   ______ _     _____                
 | |   |_ _|  ___| ____/ ___\ \ / / ___| |   | ____|               
 | |    | || |_  |  _|| |    \ V / |   | |   |  _|                 
 | |___ | ||  _| | |__| |___  | || |___| |___| |___                
 |_____|___|_|   |_____\____| |_| \____|_____|_____|               
  __  __    _    _   _    _    ____ _____ __  __ _____ _   _ _____ 
 |  \/  |  / \  | \ | |  / \  / ___| ____|  \/  | ____| \ | |_   _|
 | |\/| | / _ \ |  \| | / _ \| |  _|  _| | |\/| |  _| |  \| | | |  
 | |  | |/ ___ \| |\  |/ ___ \ |_| | |___| |  | | |___| |\  | | |  
 |_|  |_/_/   \_\_| \_/_/   \_\____|_____|_|  |_|_____|_| \_| |_|  
  ______   ______ _____ _____ __  __                               
 / ___\ \ / / ___|_   _| ____|  \/  |                              
 \___ \\ V /\___ \ | | |  _| | |\/| |                              
  ___) || |  ___) || | | |___| |  | |                              
 |____/ |_| |____/ |_| |_____|_|  |_|                              
                                                                   




This research introduces the Cluster Lifecycle Management System (CLMS), 
a preemptive approach to container lifecycle management in Kubernetes

Creation date: 04.23.25 - alhumaw


"""



from datetime import datetime, timedelta, timezone
from time import sleep
from dataclasses import dataclass
from os import environ, getpid
from subprocess import getstatusoutput
from argparse import ArgumentParser, RawTextHelpFormatter, Namespace as ArgNamespace
from concurrent.futures import ProcessPoolExecutor, as_completed, wait, ALL_COMPLETED
import logging

try:
    from termcolor import colored
except ImportError as no_termcolor:
    raise SystemExit("The termcolor library must be installed.\n"
                     "Install it with python3 -m pip install termcolor")
try:
    from tabulate import tabulate
except ImportError as no_tabulate:
    raise SystemExit("The tabulate library must be installed.\n"
                     "Install it with python3 -m pip install tabulate")
try:
    from kubernetes import client, config
except ImportError as no_kube:
    raise SystemExit("The kubernetes library must be installed.\n"
                     "Install it with python3 -m pip install kubernetes")
    
def parse_command_line() -> ArgNamespace:
    """Parse any provided command line arguments and return the namespace."""
    parser = ArgumentParser(description=__doc__,
                            formatter_class=RawTextHelpFormatter)
    require = parser.add_argument_group("required arguments")
    require.add_argument("-n", "--namespaces",
                         required=True,
                         help="Selected namespaces for CLMS to monitor")
    parser.add_argument("-e", "--exclude",
                        help="Comma separated list of deployments to exclude",
                        default="")
    parser.add_argument("-d", "--debug",
                        help="Enable API debugging",
                        action="store_true",
                        default=False)
    parsed = parser.parse_args()

    if parsed.debug:
        logging.basicConfig(level=logging.DEBUG,
                            format='%(asctime)s [PID %(process)d] %(levelname)s: %(message)s')
    else:
        logging.basicConfig(level=logging.INFO,
                            format='%(asctime)s [PID %(process)d] %(levelname)s: %(message)s')
    return parsed

@dataclass
class Deployment:
    name: str
    label: str

@dataclass
class KubernetesNamespace:
    """Kubernetes Namespace Dataclass"""
    name: str
    deployments: list[Deployment]

def find_all_namespaces(v1: client.CoreV1Api) -> list:
    """Return a list of all namespace names."""
    namespace_api = v1.list_namespace(watch=False)
    namespaces = [ns.metadata.name for ns in namespace_api.items]
    logging.debug(f"Found namespaces: {namespaces}")
    return namespaces

def apoptosis(namespace: str, deployment_label: str) -> None:
    """
    Deletes the oldest half of the pods from a deployment.
    """
    logging.debug(f"Running apoptosis for namespace {namespace} with label {deployment_label}")
    status, pods = getstatusoutput(
        f"kubectl get pods -n {namespace} -l {deployment_label} --sort-by=.metadata.creationTimestamp --no-headers | awk '{{print $1}}'"
    )
    pod_list = pods.strip().split('\n')
    pod_count = len(pod_list)
    old_pods = pod_list[:pod_count // 2]
    if old_pods:
        old_pods_str = " ".join(old_pods)
        status, output = getstatusoutput(f"kubectl delete pod {old_pods_str} -n {namespace}")
        logging.debug(f"Apoptosis output: {output}")
        print(output)
    else:
        logging.debug(f"No pods to delete for {namespace} with label {deployment_label}")
        print(f"No pods to delete in namespace {namespace} with label {deployment_label}")

def scale_deployment(v1: client.AppsV1Api, namespace: str, deployment_name: str, target_replicas: int) -> None:
    """Scales a deployment to a specified number of replicas."""
    logging.debug(f"Scaling deployment {deployment_name} in namespace {namespace} to {target_replicas}")
    print(f"Scaling deployment {deployment_name} in namespace {namespace} to {target_replicas} replicas")
    status, output = getstatusoutput(
        f"kubectl scale deployment {deployment_name} --replicas={target_replicas} -n {namespace}"
    )
    logging.debug(f"Scale command output: {output}")
    print("Command output:", output)

def scale_out_deployment(v1: client.AppsV1Api, namespace: str, deployment_name: str, original_replicas: int) -> None:
    """Scales out a deployment to double its original replica count."""
    target = original_replicas + 1
    logging.debug(f"Scaling out {deployment_name} from {original_replicas} to {target}")
    print(f"Scaling out {deployment_name} (from {original_replicas} to {target})")
    scale_deployment(v1, namespace, deployment_name, target)

def scale_in_deployment(v1: client.AppsV1Api, namespace: str, deployment_name: str, original_replicas: int) -> None:
    """Scales in a deployment back to its original replica count."""
    logging.debug(f"Scaling in {deployment_name} back to {original_replicas}")
    print(f"Scaling in {deployment_name} back to {original_replicas} replicas")
    scale_deployment(v1, namespace, deployment_name, original_replicas)

def aggregate_deployments_by_namespace(v1: client.AppsV1Api, namespace: str) -> list:
    """
    For each deployment in the namespace, grab the first label from its selector
    and store that (as a key=value string) along with the deployment's name.
    """
    logging.debug(f"Aggregating deployments for namespace {namespace}")
    deployment_api = v1.list_namespaced_deployment(namespace=namespace)
    deployments = []
    for deployment in deployment_api.items:
        selector_labels = deployment.spec.selector.match_labels
        if not selector_labels:
            selector_labels = deployment.spec.template.metadata.labels
        first_label_key, first_label_value = next(iter(selector_labels.items()))
        label_selector = f"{first_label_key}={first_label_value}"
        deployed = Deployment(name=deployment.metadata.name, label=label_selector)
        deployments.append(deployed)
    logging.debug(f"Deployments aggregated: {[d.name for d in deployments]}")
    return deployments

def build_namespaces(v1: client.AppsV1Api, namespaces: list) -> list:
    """Build KubernetesNamespace dataclass objects."""
    kube_namespaces = []
    for ns in namespaces:
        deployments = aggregate_deployments_by_namespace(v1, ns)
        kube_namespaces.append(KubernetesNamespace(name=ns, deployments=deployments))
    logging.debug(f"Built namespace objects: {[ns.name for ns in kube_namespaces]}")
    return kube_namespaces

def process_namespace(namespace_obj: KubernetesNamespace, exclusions: list, cur_deployment_list: list[str] = None) -> str:
    """
    Process a single namespace: for each deployment (if not excluded by loose matching)
    record the original replica count, scale-out, run apoptosis, then scale back in.
    """
    from os import environ
    from kubernetes import client, config
    config.load_kube_config(config_file=environ["KUBECONFIG"])
    apps_v1 = client.AppsV1Api()
    logging.debug(f"Process_namespace PID {getpid()} started for namespace {namespace_obj.name}")
    
    if cur_deployment_list:
        logging.debug(f"Processing a chunk of deployments: {[d.name for d in cur_deployment_list]}")
        print(f"Processing namespace: {namespace_obj.name}")
        for deployment in cur_deployment_list:
            if any(exclusion.lower() in deployment.name.lower() for exclusion in exclusions):
                logging.debug(f"Skipping excluded deployment: {deployment.name}")
                print(f"Skipping excluded deployment: {deployment.name} in namespace {namespace_obj.name}")
                continue

            try:
                dep_obj = apps_v1.read_namespaced_deployment(name=deployment.name, namespace=namespace_obj.name)
            except Exception as e:
                logging.error(f"Error reading deployment {deployment.name}: {e}")
                continue

            original_replicas = dep_obj.status.replicas
            logging.debug(f"{deployment.name} original replica count: {original_replicas}")
            print(f"Original replica count for {deployment.name}: {original_replicas}")

            scale_out_deployment(v1=apps_v1,
                                 namespace=namespace_obj.name,
                                 deployment_name=deployment.name,
                                 original_replicas=original_replicas)
            sleep(60)

            apoptosis(namespace=namespace_obj.name, deployment_label=deployment.label)

            scale_in_deployment(v1=apps_v1,
                                namespace=namespace_obj.name,
                                deployment_name=deployment.name,
                                original_replicas=original_replicas)
        msg = f"Completed processing for namespace: {namespace_obj.name} by PID {getpid()}"
        logging.debug(msg)
        return msg
    else:
        # This branch would process all deployments if no chunk is provided.
        return f"No deployments provided for processing in namespace: {namespace_obj.name}"

def multiprocess_deployments(namespace_obj: KubernetesNamespace, exclusions: list) -> str:
    chunk_size = 10
    chunks = [namespace_obj.deployments[i:i + chunk_size] for i in range(0, len(namespace_obj.deployments), chunk_size)]
    logging.debug(f"Namespace {namespace_obj.name} has {len(namespace_obj.deployments)} deployments split into {len(chunks)} chunks.")
    results = []
    with ProcessPoolExecutor(max_workers=len(chunks)) as e:
        futures = {
            e.submit(process_namespace, namespace_obj, exclusions, chunk): chunk
                for chunk in chunks 
        }
        # wait(futures, timeout=None, return_when=ALL_COMPLETED)
        for future in as_completed(futures):
            chunk_deployments = [d.name for d in futures[future]]
            try:
                result = future.result()
                if result is not None:
                    logging.debug(f"Chunk {chunk_deployments} completed with result: {result}")
                    results.append(result)
            except Exception as exc:
                logging.error(f"Chunk {chunk_deployments} generated an exception: {exc}")
    return results[0]

def begin_clms(namespaces: list[KubernetesNamespace], exclusions: list) -> None:
    """
    Main workflow: for each cycle, assign each namespace to a separate process
    which handles its deployments concurrently.
    """
    from concurrent.futures import ProcessPoolExecutor, as_completed
    while True:
        logging.info("Starting new processing cycle...")
        with ProcessPoolExecutor(max_workers=len(namespaces)) as e:
            futures = {
                e.submit(multiprocess_deployments, ns, exclusions): ns.name
                for ns in namespaces
            }
            for future in as_completed(futures):
                ns_name = futures[future]
                try:
                    result = future.result()
                    logging.info(f"Namespace {ns_name} finished with result: {result}")
                    print(result)
                except Exception as exc:
                    logging.error(f"Namespace {ns_name} generated an exception: {exc}")
        sleep(300)

def load_k8s_client() -> tuple:
    """Instantiates the Kubernetes client."""
    config.load_kube_config(config_file=environ["KUBECONFIG"])
    return client.CoreV1Api(), client.AppsV1Api()

def main():
    # init kube / parse cmdline.
    core_api, apps_api = load_k8s_client()
    args = parse_command_line()
    
    # validate user input.
    all_namespaces = find_all_namespaces(core_api)
    namespace_list = [n.strip() for n in args.namespaces.split(",")] 
    for ns in namespace_list:
        if ns not in all_namespaces:
            exit(f"ERROR - Namespace {ns} not found")
    logging.info(f"Namespaces to process: {namespace_list}")
    print("Namespaces to process:", namespace_list)
    
    # build obj.
    namespaces = build_namespaces(apps_api, namespace_list)
    
    # build exclusions.
    exclusions = [e.strip() for e in args.exclude.split(",")] if args.exclude else []
    logging.debug(f"Exclusions: {exclusions}")
    
    # begin.
    begin_clms(namespaces, exclusions)

if __name__ == "__main__":
    main()

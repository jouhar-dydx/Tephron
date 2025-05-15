# src/aws/ec2/cost_estimator_cli.py
import logging
from src.aws.ec2.cost_estimator import EC2CostEstimator
from src.aws.ec2.scanner import get_all_regions, EC2Scanner

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    regions = get_all_regions()
    logger.info(f"[+] Found {len(regions)} active regions")
    
    cost_estimator = EC2CostEstimator()
    
    all_instances = []
    for region in regions:
        scanner = EC2Scanner(region)
        instances = scanner.scan_instances()
        analyzed = [cost_estimator.estimate_monthly_cost(inst) for inst in instances]
        all_instances.extend(analyzed)
        logger.info(f"[+] Analyzed {len(instances)} instance(s) in {region}")
    
    # Save summary report
    output_file = f"data/output/ec2/cost_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    save_json(all_instances, output_file)
    
    # Log underutilized instances
    underutilized = [inst for inst in all_instances if inst.get("Underutilized")]
    logger.info(f"[+] Identified {len(underutilized)} underutilized instances")
    
if __name__ == "__main__":
    main()
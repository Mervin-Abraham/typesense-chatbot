#!/usr/bin/env python3

import requests
import time
import logging
import json
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ServiceMonitor:
	def __init__(self, service_url: str, api_key: str = None):
		self.service_url = service_url
		self.headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}

	def check_health(self) -> Dict:
		'''
			Check service health
		'''
		
		try:
			response = requests.get(f"{self.service_url}/health", timeout=10)
			return {
				"status": "up" if response.status_code == 200 else "down",
				"response_time": response.elapsed.total_seconds(),
				"data": response.json() if response.status_code == 200 else None,
				"error": None
			}
		except Exception as e:
			return {
				"status": "down",
				"response_time": None,
				"data": None,
				"error": str(e)
			}

	def check_embedding_performance(self) -> Dict:
		'''
			Test embedding generation performance
		'''
		
		try:
			test_data = {"text": "This is a performance test for embedding generation"}
			start_time = time.time()

			response = requests.post(
				f"{self.service_url}/api/v1/embed-snippet",
				headers=self.headers,
				json=test_data,
				timeout=30
			)

			total_time = time.time() - start_time

			if response.status_code == 200:
				result = response.json()
				return {
					"status": "ok",
					"embedding_time_ms": result["processing_time_ms"],
					"total_time_ms": total_time * 1000,
					"model_version": result["model_version"],
					"error": None
				}
			else:
				return {
					"status": "error",
					"error": f"HTTP {response.status_code}: {response.text}"
				}
		except Exception as e:
			return {
				"status": "error",
				"error": str(e)
			}

	def check_search_performance(self) -> Dict:
		'''
			Test search performance
		'''
		
		try:
			search_data = {
				"query": "machine learning algorithms",
				"limit": 5
			}
			start_time = time.time()

			response = requests.post(
				f"{self.service_url}/api/v1/search-snippets",
				headers=self.headers,
				json=search_data,
				timeout=30
			)

			total_time = time.time() - start_time

			if response.status_code == 200:
				result = response.json()
				return {
					"status": "ok",
					"search_time_ms": result["search_time_ms"],
					"total_time_ms": total_time * 1000,
					"results_found": result["total_found"],
					"error": None
				}
			else:
				return {
					"status": "error",
					"error": f"HTTP {response.status_code}: {response.text}"
				}
		except Exception as e:
			return {
				"status": "error",
				"error": str(e)
			}

	def run_full_health_check(self) -> Dict:
		'''
			Run comprehensive health check
		'''
		
		logger.info("Running full health check...")

		results = {
			"timestamp": datetime.now().isoformat(),
			"service_url": self.service_url,
			"checks": {}
		}

		# Basic health check
		results["checks"]["health"] = self.check_health()

		# Only run performance tests if basic health is ok
		if results["checks"]["health"]["status"] == "up":
			results["checks"]["embedding_performance"] = self.check_embedding_performance()
			results["checks"]["search_performance"] = self.check_search_performance()

		# Overall status
		all_ok = all(
			check["status"] in ["up", "ok"]
			for check in results["checks"].values()
		)
		results["overall_status"] = "healthy" if all_ok else "unhealthy"

		return results

	def continuous_monitoring(self, interval_seconds: int = 60):
		'''
			Run continuous monitoring
		'''
		
		logger.info(f"Starting continuous monitoring (interval: {interval_seconds}s)")

		while True:
			try:
				results = self.run_full_health_check()

				# Log results
				if results["overall_status"] == "healthy":
					logger.info("✓ All systems healthy")
				else:
					logger.warning("⚠ System issues detected")
					for check_name, check_result in results["checks"].items():
						if check_result["status"] not in ["up", "ok"]:
							logger.error(f"  {check_name}: {check_result.get('error', 'Unknown error')}")

				# You could also send alerts here or write to monitoring system

			except Exception as e:
				logger.error(f"Monitoring error: {e}")

			time.sleep(interval_seconds)

def main():
	SERVICE_URL = "http://localhost:8000"
	API_KEY = "your-secret-api-key"  # Optional

	monitor = ServiceMonitor(SERVICE_URL, API_KEY)

	# Run one-time health check
	results = monitor.run_full_health_check()
	print(json.dumps(results, indent=2))

	# Uncomment for continuous monitoring
	# monitor.continuous_monitoring(interval_seconds=60)

if __name__ == "__main__":
	main()
#!/usr/bin/env python3

import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
API_KEY = "your-secret-api-key"
HEADERS = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

def test_health():
	'''
		Test health endpoint
	'''
		
	print("Testing health endpoint...")
	response = requests.get("http://localhost:8000/health")
	print(f"Health Status: {response.status_code}")
	print(f"Response: {response.json()}")
	return response.status_code == 200

def test_embedding():
	'''
		Test embedding generation
	'''
		
	print("\nTesting embedding generation...")
	data = {"text": "This is a test snippet about machine learning"}

	response = requests.post(f"{BASE_URL}/embed-snippet", headers=HEADERS, json=data)
	print(f"Embedding Status: {response.status_code}")

	if response.status_code == 200:
		result = response.json()
		print(f"Embedding dimension: {len(result['embedding'])}")
		print(f"Processing time: {result['processing_time_ms']:.2f}ms")
		print(f"Model version: {result['model_version']}")
	else:
		print(f"Error: {response.text}")

	return response.status_code == 200

def test_indexing():
	'''
		Test snippet indexing
	'''
		
	print("\nTesting snippet indexing...")

	snippet_data = {
		"snippet": {
			"id": "test-snippet-1",
			"title": "Machine Learning Basics",
			"description": "An introduction to machine learning concepts and algorithms",
			"created_on": datetime.now().isoformat(),
			"snippet_type": "tutorial",
			"published": True,
			"product_category_ids": [1, 2, 3]
		}
	}

	response = requests.post(f"{BASE_URL}/index-snippet", headers=HEADERS, json=snippet_data)
	print(f"Indexing Status: {response.status_code}")

	if response.status_code == 200:
		result = response.json()
		print(f"Success: {result['success']}")
		print(f"Snippet ID: {result['snippet_id']}")
		print(f"Processing time: {result['processing_time_ms']:.2f}ms")
	else:
		print(f"Error: {response.text}")

	return response.status_code == 200

def test_search():
	'''
		Test snippet search
	'''
		
	print("\nTesting snippet search...")

	search_data = {
		"query": "machine learning",
		"limit": 5,
		"published_only": True
	}

	# Test text search
	response = requests.post(f"{BASE_URL}/search-snippets?search_type=text",
						   headers=HEADERS, json=search_data)
	print(f"Text Search Status: {response.status_code}")

	if response.status_code == 200:
		result = response.json()
		print(f"Found {result['total_found']} results")
		print(f"Search time: {result['search_time_ms']:.2f}ms")
		print(f"Query by: {result['query_by']}")
	else:
		print(f"Error: {response.text}")

	# Test vector search
	response = requests.post(f"{BASE_URL}/search-snippets?search_type=vector",
						   headers=HEADERS, json=search_data)
	print(f"Vector Search Status: {response.status_code}")

	if response.status_code == 200:
		result = response.json()
		print(f"Vector search found {result['total_found']} results")
		print(f"Search time: {result['search_time_ms']:.2f}ms")

	return response.status_code == 200

def test_batch_indexing():
	'''
		Test batch indexing
	'''
		
	print("\nTesting batch indexing...")

	snippets = []
	for i in range(3):
		snippets.append({
			"id": f"batch-test-{i}",
			"title": f"Test Snippet {i}",
			"description": f"This is test snippet number {i} for batch indexing",
			"created_on": datetime.now().isoformat(),
			"snippet_type": "test",
			"published": True,
			"product_category_ids": [i + 1]
		})

	batch_data = {"snippets": snippets, "batch_size": 2}

	response = requests.post(f"{BASE_URL}/batch-index", headers=HEADERS, json=batch_data)
	print(f"Batch Indexing Status: {response.status_code}")

	if response.status_code == 200:
		result = response.json()
		print(f"Total processed: {result['total_processed']}")
		print(f"Successful: {result['successful']}")
		print(f"Failed: {result['failed']}")
		print(f"Processing time: {result['processing_time_ms']:.2f}ms")
		if result['errors']:
			print(f"Errors: {result['errors']}")
	else:
		print(f"Error: {response.text}")

	return response.status_code == 200

def main():
	'''
		Run all tests
	'''
		
	print("=== Embedding + RAG Service Tests ===")

	tests = [
		("Health Check", test_health),
		("Embedding Generation", test_embedding),
		("Snippet Indexing", test_indexing),
		("Search Functionality", test_search),
		("Batch Indexing", test_batch_indexing)
	]

	results = {}
	for test_name, test_func in tests:
		try:
			results[test_name] = test_func()
		except Exception as e:
			print(f"Test {test_name} failed with exception: {e}")
			results[test_name] = False

		time.sleep(1)  # Brief pause between tests

	print("\n=== Test Results ===")
	for test_name, passed in results.items():
		status = "PASSED" if passed else "FAILED"
		print(f"{test_name}: {status}")

	all_passed = all(results.values())
	print(f"\nOverall: {'ALL TESTS PASSED' if all_passed else 'SOME TESTS FAILED'}")

	return all_passed

if __name__ == "__main__":
	main()
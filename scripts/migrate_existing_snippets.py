#!/usr/bin/env python3

import asyncio
import json
import logging
from datetime import datetime
from typing import List, Dict
import requests

# This script helps migrate existing snippets from your legacy system
# to the new embedding service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SnippetMigrator:
	def __init__(self, service_url: str, api_key: str):
		self.service_url = service_url
		self.headers = {
			"Authorization": f"Bearer {api_key}",
			"Content-Type": "application/json"
		}

	def load_snippets_from_json(self, file_path: str) -> List[Dict]:
		'''
			Load snippets from JSON file
		'''
		
		with open(file_path, 'r') as f:
			return json.load(f)

	def convert_snippet_format(self, legacy_snippet: Dict) -> Dict:
		'''
			Convert legacy snippet format to new format
		'''
		
		return {
			"id": str(legacy_snippet.get("id")),
			"title": legacy_snippet.get("title", ""),
			"description": legacy_snippet.get("description", ""),
			"created_on": legacy_snippet.get("created_on", datetime.now().isoformat()),
			"snippet_type": legacy_snippet.get("type", "general"),
			"published": legacy_snippet.get("published", True),
			"product_category_ids": legacy_snippet.get("categories", [])
		}

	def migrate_batch(self, snippets: List[Dict], batch_size: int = 10) -> bool:
		'''
			Migrate a batch of snippets
		'''
		
		try:
			# Convert to new format
			converted_snippets = [self.convert_snippet_format(s) for s in snippets]

			# Send batch request
			batch_data = {
				"snippets": converted_snippets,
				"batch_size": batch_size
			}

			response = requests.post(
				f"{self.service_url}/api/v1/batch-index",
				headers=self.headers,
				json=batch_data,
				timeout=300  # 5 minutes timeout for large batches
			)

			if response.status_code == 200:
				result = response.json()
				logger.info(f"Batch migration completed: {result['successful']} successful, {result['failed']} failed")
				if result['errors']:
					logger.error(f"Errors: {result['errors']}")
				return result['failed'] == 0
			else:
				logger.error(f"Batch migration failed: {response.status_code} - {response.text}")
				return False

		except Exception as e:
			logger.error(f"Migration error: {e}")
			return False

	def migrate_from_database(self, db_config: Dict):
		'''
			Migrate snippets directly from database
		
			# This would connect to your existing database
			# and fetch snippets in batches

			# Example implementation (you'll need to adapt to your DB):
		'''
		
		import psycopg2  # or your database driver

		conn = psycopg2.connect(**db_config)
		cursor = conn.cursor()

		# Fetch snippets in batches
		offset = 0
		batch_size = 50

		while True:
			cursor.execute('''
				SELECT id, title, description, created_on, snippet_type, published
				FROM snippets
				WHERE published = true
				ORDER BY id
				LIMIT %s OFFSET %s
			''', (batch_size, offset))

			rows = cursor.fetchall()
			if not rows:
				break

			# Convert to dict format
			snippets = []
			for row in rows:
				snippets.append({
					'id': row[0],
					'title': row[1],
					'description': row[2],
					'created_on': row[3].isoformat(),
					'snippet_type': row[4],
					'published': row[5]
				})

			# Migrate batch
			success = self.migrate_batch(snippets)
			if not success:
				logger.error(f"Failed to migrate batch at offset {offset}")
				break

			offset += batch_size
			logger.info(f"Migrated {offset} snippets so far...")

		conn.close()
		
		pass

def main():
	SERVICE_URL = "http://localhost:8000"
	API_KEY = "your-secret-api-key"

	migrator = SnippetMigrator(SERVICE_URL, API_KEY)

	# Example: Migrate from JSON file
	try:
		snippets = migrator.load_snippets_from_json("legacy_snippets.json")
		logger.info(f"Loaded {len(snippets)} snippets from JSON")

		# Migrate in batches
		batch_size = 20
		for i in range(0, len(snippets), batch_size):
			batch = snippets[i:i + batch_size]
			logger.info(f"Migrating batch {i//batch_size + 1} ({len(batch)} snippets)")

			success = migrator.migrate_batch(batch)
			if not success:
				logger.error("Migration failed, stopping")
				break

		logger.info("Migration completed!")

	except FileNotFoundError:
		logger.info("No JSON file found, you can implement database migration instead")

		# Example database config
		db_config = {
			'host': 'localhost',
			'database': 'your_db',
			'user': 'your_user',
			'password': 'your_password'
		}
		# migrator.migrate_from_database(db_config)

if __name__ == "__main__":
	main()
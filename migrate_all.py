#!/usr/bin/env python3
"""
Unified migration runner to execute all migration scripts
"""
import sys
import logging
import importlib.util

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# List of migration modules and their entry functions
MIGRATIONS = [
    ('migrate_db', 'migrate_db'),
    ('migrate_email', 'migrate_database'),
    ('migrate_parent_warning', 'migrate_database'),
    ('migrate_duplicate_warning', 'migrate_database'),
    ('migrate_add_note', 'migrate_add_note_column'),
    ('migrate_audit_log', 'migrate_audit_log'),
    ('migrate_newsletter_integer', 'migrate_newsletter_to_integer'),
    ('migrate_remove_email_template', 'migrate_database'),
]

def run_migrations(db_path):
    """Run all migrations on the specified database"""
    logger.info(f"Starting migrations for {db_path}...")
    
    for module_name, function_name in MIGRATIONS:
        try:
            # Import module dynamically
            if module_name in sys.modules:
                module = sys.modules[module_name]
            else:
                spec = importlib.util.spec_from_file_location(module_name, f"{module_name}.py")
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    sys.modules[module_name] = module
                    spec.loader.exec_module(module)
                else:
                    logger.error(f"Could not load module {module_name}")
                    continue
            
            # Get migration function
            if hasattr(module, function_name):
                migration_func = getattr(module, function_name)
                logger.info(f"Running {module_name}.{function_name}...")
                migration_func(db_path)
            else:
                logger.warning(f"Function {function_name} not found in {module_name}")
                
        except Exception as e:
            logger.error(f"Error running migration {module_name}: {e}")
            # We continue with other migrations even if one fails
            
    logger.info(f"Migrations completed for {db_path}")

if __name__ == '__main__':
    databases = ['applications_test.db', 'applications.db']
    for db in databases:
        run_migrations(db)

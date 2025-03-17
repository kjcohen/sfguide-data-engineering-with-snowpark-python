#------------------------------------------------------------------------------
# Hands-On Lab: Data Engineering with Snowpark
# Script:       06_orders_process_sp/app.py
# Author:       Jeremiah Hansen, Caleb Baechtold
# Last Updated: 1/9/2023
#------------------------------------------------------------------------------

# SNOWFLAKE ADVANTAGE: Python Stored Procedures

import time
from snowflake.snowpark import Session
#import snowflake.snowpark.types as T
import snowflake.snowpark.functions as F



def main(session: Session) -> str:
    return f"Successfully processed ORDERS!"
    # Create the ORDERS table and ORDERS_STREAM stream if they don't exist
#     if not table_exists(session, schema='HARMONIZED', name='ORDERS'):
#         create_orders_table(session)
#         create_orders_stream(session)

#     # Process data incrementally
#     merge_order_updates(session)
# #    session.table('HARMONIZED.ORDERS').limit(5).show()

#     return f"Successfully processed ORDERS!"


# For local debugging
# Be aware you may need to type-convert arguments if you add input parameters
if __name__ == '__main__':
    # Create a local Snowpark session
    return f"Successfully processed ORDERS!"

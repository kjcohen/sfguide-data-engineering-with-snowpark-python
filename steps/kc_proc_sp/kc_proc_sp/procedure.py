#------------------------------------------------------------------------------
# Hands-On Lab: Data Engineering with Snowpark
# Script:       06_orders_process_sp/app.py
# Author:       Jeremiah Hansen, Caleb Baechtold
# Last Updated: 1/9/2023
#------------------------------------------------------------------------------

# SNOWFLAKE ADVANTAGE: Python Stored Procedures

import time
import sys
from snowflake.snowpark import Session
#import snowflake.snowpark.types as T
import snowflake.snowpark.functions as F



def main(inputstring: str) -> str:
    print('test')
    return str(inputstring)


# For local debugging
# Be aware you may need to type-convert arguments if you add input parameters
if __name__ == '__main__':
    # Create a local Snowpark session
    with Session.builder.getOrCreate() as session:
        import sys
        if len(sys.argv) > 1:
            print(main(session, *sys.argv[1:]))  # type: ignore
        else:
            print(main(session))  # type: ignore

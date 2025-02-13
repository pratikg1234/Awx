import pyodbc
 
# SQL Server connection details
SQL_SERVER = "20.102.105.60"
SQL_DATABASE = "master"
SQL_USERNAME = "rajusql"
SQL_PASSWORD = "Raju@2002"
 
def sql_server_connect():
    """Connect to SQL Server using pyodbc"""
    try:
        conn = pyodbc.connect(
            f"DRIVER={{SQL Server}};SERVER={SQL_SERVER};DATABASE={SQL_DATABASE};"
            f"UID={SQL_USERNAME};PWD={SQL_PASSWORD}"
        )
        print("[✅] Connected to SQL Server successfully")
        return conn
    except Exception as e:
        print(f"[❌] SQL Server Connection Error: {e}")
        return None
 
def check_db_space(conn):
    """Check database space utilization"""
    query = """
    SELECT DB_NAME(database_id) AS DatabaseName,
           SUM(size * 8) / 1024 AS TotalSizeMB
    FROM sys.master_files
    GROUP BY database_id;
    """
    cursor = conn.cursor()
    cursor.execute(query)
    results = cursor.fetchall()
    print("\n📊 Database Space Utilization:")
    for row in results:
        print(f" - {row.DatabaseName}: {row.TotalSizeMB} MB")
 
def check_deadlocks(conn):
    """Check for deadlocks"""
    query = "SELECT * FROM sys.dm_tran_locks WHERE request_status = 'WAIT'"
    cursor = conn.cursor()
    cursor.execute(query)
    results = cursor.fetchall()
    print("\n🚨 Deadlocks:")
    if results:
        for row in results:
            print(f" - Lock ID: {row.lock_owner_address}, Object ID: {row.resource_description}")
    else:
        print(" - No deadlocks detected")
 
def check_job_activities(conn):
    """Check SQL Server Agent job activities"""
    try:
        query = """
        SELECT j.job_id, j.name, j.enabled,
               MAX(h.run_status) AS last_run_status
        FROM msdb.dbo.sysjobs j
        LEFT JOIN msdb.dbo.sysjobhistory h ON j.job_id = h.job_id
        WHERE h.step_id = 0
        GROUP BY j.job_id, j.name, j.enabled;
        """
        cursor = conn.cursor()
        cursor.execute(query)
        results = cursor.fetchall()
 
        print(f"[ℹ️] Job activities query returned {len(results)} rows.")
 
        if not results:
            print("[⚠️] No job activities found. Ensure SQL Server Agent is running.")
            return
 
        print("\n🛠 SQL Server Agent Job Activities:")
        for row in results:
            # Map run_status to readable outcome
            outcome = {
                0: "Failed",
                1: "Succeeded",
                2: "Retry",
                3: "Canceled"
            }.get(row.last_run_status, "Unknown")
           
            print(f" - Job: {row.name} | Enabled: {row.enabled} | Last Outcome: {outcome}")
   
    except Exception as e:
        print(f"[❌] Error fetching job activities: {e}")
 
def check_db_health(conn):
    """Check SQL Server health status"""
    query = """
    SELECT 
    db.name AS DatabaseName,
    db.state_desc AS Status,
    -- Active Requests for the specific database
    (SELECT COUNT(*) 
     FROM sys.dm_exec_requests r 
     WHERE r.database_id = db.database_id) AS ActiveRequests,

    -- Active User Connections for the specific database
    (SELECT COUNT(*) 
     FROM sys.dm_exec_sessions s 
     WHERE s.is_user_process = 1 AND s.database_id = db.database_id) AS ActiveUserConnections,

    -- Pending Requests for the specific database
    (SELECT COUNT(*) 
     FROM sys.dm_os_waiting_tasks w 
     JOIN sys.dm_exec_sessions s ON w.session_id = s.session_id
     WHERE s.database_id = db.database_id) AS PendingRequests,

    -- CPU Queue Length for the whole system (this doesn't depend on the database)
    (SELECT COUNT(*) 
     FROM sys.dm_os_performance_counters
     WHERE counter_name = 'Processor Queue Length') AS CPUQueueLength
FROM sys.databases db;
    """
    cursor = conn.cursor()
    cursor.execute(query)
    results = cursor.fetchall()
    print("\n🩺 Database Health Check:")
    for row in results:
        print(f" - Database: {row.DatabaseName}")
        print(f"   - Status: {row.Status}")
        print(f"   - Active Requests: {row.ActiveRequests}")
        print(f"   - Active User Connections: {row.ActiveUserConnections}")
        print(f"   - Pending Requests: {row.PendingRequests}")
        print(f"   - CPU Queue Length: {row.CPUQueueLength}\n")
       
# Main execution
if __name__ == "__main__":
 
    sql_conn = sql_server_connect()
    if sql_conn:
        check_db_space(sql_conn)
        check_deadlocks(sql_conn)
        check_job_activities(sql_conn)
        check_db_health(sql_conn)  # Added Health Check Function
        sql_conn.close()
 
 

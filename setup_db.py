import sqlite3
import random
import uuid
from datetime import datetime, timedelta

def create_db():
    conn = sqlite3.connect('remedy_mock.db')
    c = conn.cursor()

    # Drop existing tables
    c.execute('DROP TABLE IF EXISTS hpd_help_desk')
    c.execute('DROP TABLE IF EXISTS hpd_worklog')
    c.execute('DROP TABLE IF EXISTS ctm_people')
    c.execute('DROP TABLE IF EXISTS ctm_support_group_assoc')
    c.execute('DROP TABLE IF EXISTS sys_status_reason')

    c.execute('DROP TABLE IF EXISTS users')
    c.execute('DROP TABLE IF EXISTS chat_sessions')
    c.execute('DROP TABLE IF EXISTS chat_messages')
    c.execute('DROP TABLE IF EXISTS dashboards')
    c.execute('DROP TABLE IF EXISTS dashboard_widgets')

    # Application State Tables (For BI persistence)
    c.execute('''
        CREATE TABLE users (
            id TEXT PRIMARY KEY,
            username TEXT UNIQUE,
            password_hash TEXT,
            created_at DATETIME
        )
    ''')

    c.execute('''
        CREATE TABLE chat_sessions (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            title TEXT,
            created_at DATETIME,
            updated_at DATETIME,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')

    c.execute('''
        CREATE TABLE chat_messages (
            id TEXT PRIMARY KEY,
            session_id TEXT,
            role TEXT,
            content TEXT,
            charts_json TEXT,
            created_at DATETIME,
            FOREIGN KEY(session_id) REFERENCES chat_sessions(id)
        )
    ''')

    c.execute('''
        CREATE TABLE dashboards (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            name TEXT,
            created_at DATETIME,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')

    c.execute('''
        CREATE TABLE dashboard_widgets (
            id TEXT PRIMARY KEY,
            dashboard_id TEXT,
            title TEXT,
            type TEXT,
            sql_query TEXT,
            x_col TEXT,
            y_col TEXT,
            FOREIGN KEY(dashboard_id) REFERENCES dashboards(id)
        )
    ''')

    # 1. CTM:People
    c.execute('''
        CREATE TABLE ctm_people (
            Person_ID TEXT PRIMARY KEY,
            Submit_Date DATETIME,
            Login_ID TEXT,
            Last_Modified_Date DATETIME,
            Site TEXT,
            Department TEXT,
            Region TEXT,
            Site_Group TEXT,
            Company TEXT,
            Organization TEXT,
            Last_Name TEXT,
            First_Name TEXT,
            Title TEXT,
            Desk_Location TEXT,
            Email_Address TEXT,
            Corporate_ID TEXT,
            Phone_Number_Business TEXT,
            VIP TEXT
        )
    ''')

    # 2. CTM:Support Group Assoc LookUp
    c.execute('''
        CREATE TABLE ctm_support_group_assoc (
            Support_Group_Assoc_LookUp_ID TEXT PRIMARY KEY,
            Company TEXT,
            Support_Organization TEXT,
            Support_Group_Name TEXT,
            Full_Name TEXT,
            Support_Group_ID TEXT,
            Person_ID TEXT,
            FOREIGN KEY(Person_ID) REFERENCES ctm_people(Person_ID)
        )
    ''')

    # 3. SYS:Status Reason Menu Items
    c.execute('''
        CREATE TABLE sys_status_reason (
            Status_Reason_ID TEXT PRIMARY KEY,
            Submit_Date DATETIME,
            Last_Modified_Date DATETIME,
            Status_Reason_Menu_Item TEXT,
            Selection_Code TEXT
        )
    ''')

    # 4. HPD:Help Desk (Incident)
    c.execute('''
        CREATE TABLE hpd_help_desk (
            Entry_ID TEXT PRIMARY KEY,
            Submit_Date DATETIME,
            Assignee_Login_ID TEXT,
            Last_Modified_By TEXT,
            Last_Modified_Date DATETIME,
            Status TEXT,
            Customer_Site TEXT,
            Site_Group TEXT,
            Service TEXT,
            CI TEXT,
            Summary TEXT,
            Company TEXT,
            City TEXT,
            Organization TEXT,
            Assigned_Support_Organization TEXT,
            Last_Name TEXT,
            First_Name TEXT,
            VIP TEXT,
            Street TEXT,
            Zip_Postal_Code TEXT,
            Assigned_Group_ID TEXT,
            Person_ID TEXT,
            Incident_Type TEXT,
            Status_Reason TEXT,
            Notes TEXT,
            Resolution TEXT,
            Incident_ID TEXT,
            Urgency TEXT,
            Impact TEXT,
            Priority TEXT,
            Reported_Source TEXT,
            Assigned_Group TEXT,
            Full_Name TEXT,
            Closed_Date DATETIME,
            SLM_Status TEXT,
            Direct_Contact_Internet_Email TEXT,
            Target_Date DATETIME,
            FOREIGN KEY(Person_ID) REFERENCES ctm_people(Person_ID)
        )
    ''')

    # 5. HPD:Worklog
    c.execute('''
        CREATE TABLE hpd_worklog (
            Work_Log_ID TEXT PRIMARY KEY,
            Submit_Date DATETIME,
            Last_Modified_By TEXT,
            Last_Modified_Date DATETIME,
            Summary TEXT,
            Notes TEXT,
            Work_Log_Submit_Date DATETIME,
            Submitter TEXT,
            Incident_Number TEXT,
            Activity_Type TEXT,
            Source TEXT,
            View_Access TEXT,
            Locked TEXT,
            Work_Log_Date DATETIME,
            FOREIGN KEY(Incident_Number) REFERENCES hpd_help_desk(Incident_ID)
        )
    ''')

    # --- Seed Data Generation ---

    # CTM:People Seed
    companies = ['Acme Corp', 'Globex', 'Initech', 'Umbrella Corp']
    depts = ['IT', 'HR', 'Finance', 'Engineering', 'Sales']
    vips = ['Yes', 'No']
    people = []
    people_ids = []
    login_ids = []
    
    for i in range(1, 51):
        pid = f"PPL{str(i).zfill(8)}"
        people_ids.append(pid)
        fname = random.choice(['John', 'Jane', 'Michael', 'Sarah', 'David', 'Emily', 'Chris', 'Jessica'])
        lname = random.choice(['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis'])
        login_id = f"{fname[0].lower()}{lname.lower()}"
        login_ids.append(login_id)
        
        people.append((
            pid,
            (datetime.now() - timedelta(days=random.randint(100, 365))).strftime('%Y-%m-%d %H:%M:%S'),
            login_id,
            (datetime.now() - timedelta(days=random.randint(1, 100))).strftime('%Y-%m-%d %H:%M:%S'),
            random.choice(['New York', 'London', 'Tokyo', 'Sydney']),
            random.choice(depts),
            'AMER', 'Headquarters',
            random.choice(companies),
            'Corporate',
            lname, fname,
            'Analyst',
            f"Floor {random.randint(1,10)} Desk {random.randint(1,50)}",
            f"{login_id}@example.com",
            f"CORP{random.randint(1000,9999)}",
            f"555-{random.randint(100,999)}-{random.randint(1000,9999)}",
            random.choices(vips, weights=[5, 95])[0] # 5% are VIPs
        ))
    c.executemany('INSERT INTO ctm_people VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)', people)

    # CTM:Support Group Assoc LookUp Seed
    groups = ['Service Desk', 'Network Ops', 'Database Admins', 'SecOps', 'Application Support']
    group_ids = [f"SGP{str(i).zfill(5)}" for i in range(len(groups))]
    support_assocs = []
    for pid, fname, lname in zip(people_ids[:15], [p[11] for p in people[:15]], [p[10] for p in people[:15]]): # Make first 15 people support staff
        group_idx = random.randint(0, len(groups)-1)
        support_assocs.append((
            str(uuid.uuid4()),
            'Acme Corp', 'IT Support', groups[group_idx], f"{fname} {lname}", group_ids[group_idx], pid
        ))
    c.executemany('INSERT INTO ctm_support_group_assoc VALUES (?,?,?,?,?,?,?)', support_assocs)

    # SYS:Status Reason Seed
    reasons = [('Pending', 'Awaiting Vendor'), ('Pending', 'Awaiting User'), ('Resolved', 'Known Error'), ('Resolved', 'Workaround Provided')]
    status_reasons = []
    for i, (status, reason) in enumerate(reasons):
        status_reasons.append((f"SR{str(i).zfill(4)}", datetime.now().strftime('%Y-%m-%d %H:%M:%S'), datetime.now().strftime('%Y-%m-%d %H:%M:%S'), reason, str(i+1)))
    c.executemany('INSERT INTO sys_status_reason VALUES (?,?,?,?,?)', status_reasons)

    # HPD:Help Desk Seed
    statuses = ['New', 'Assigned', 'In Progress', 'Pending', 'Resolved', 'Closed', 'Cancelled']
    priorities = ['Critical', 'High', 'Medium', 'Low']
    urgencies = ['1-Critical', '2-High', '3-Medium', '4-Low']
    impacts = ['1-Extensive/Widespread', '2-Significant/Large', '3-Moderate/Limited', '4-Minor/Localized']
    sources = ['Phone', 'Email', 'Web', 'Walk In', 'Event Management']
    slm_statuses = ['Service Targets Met', 'Service Targets Breached', 'Service Targets Warning', 'No Service Target Attached']

    base_date = datetime.now() - timedelta(days=60)
    incidents = []
    
    for i in range(1, 251):
        inc_id = f"INC{str(i).zfill(12)}"
        entry_id = f"ENT{str(i).zfill(8)}"
        
        submit_date = base_date + timedelta(days=random.randint(0, 60), hours=random.randint(0,23))
        status = random.choice(statuses)
        priority = random.choices(priorities, weights=[5, 15, 50, 30])[0]
        
        # Pick a random requester from ctm_people
        requester = random.choice(people)
        req_pid = requester[0]
        req_lname = requester[10]
        req_fname = requester[11]
        req_company = requester[8]
        req_vip = requester[17]
        req_email = requester[14]
        
        # Pick a random assignee if not New
        assigned_group = random.choice(groups)
        assignee_login = random.choice(login_ids[:15]) if status != 'New' else None
        
        closed_date = None
        if status in ['Resolved', 'Closed']:
            closed_date = submit_date + timedelta(hours=random.randint(1, 72))
            
        target_date = submit_date + timedelta(hours=random.choice([4, 8, 24, 48]))
        
        reason = random.choice([r[1] for r in reasons if r[0] == status]) if status in ['Pending', 'Resolved'] else None

        incidents.append((
            entry_id, submit_date.strftime('%Y-%m-%d %H:%M:%S'), assignee_login, assignee_login,
            (submit_date + timedelta(hours=1)).strftime('%Y-%m-%d %H:%M:%S'),
            status, 'New York', 'AMER', 'Email Service', 'EXCH-SRV-01',
            f"Issue with {random.choice(['Exchange', 'VPN', 'SAP', 'Network', 'Laptop'])}",
            req_company, 'New York', 'Corporate', 'IT Support', req_lname, req_fname, req_vip,
            '123 Main St', '10001', 'SGP00001', req_pid, 'User Service Restoration', reason,
            'Initial troubleshooting steps performed.', 'Rebooted server.' if closed_date else None,
            inc_id, random.choice(urgencies), random.choice(impacts), priority, random.choice(sources),
            assigned_group, f"{req_fname} {req_lname}", closed_date.strftime('%Y-%m-%d %H:%M:%S') if closed_date else None,
            random.choice(slm_statuses), req_email, target_date.strftime('%Y-%m-%d %H:%M:%S')
        ))
    c.executemany('INSERT INTO hpd_help_desk VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)', incidents)

    # HPD:Worklog Seed
    worklog_types = ['General Information', 'Incident Task/Action', 'Customer Communication', 'Resolution Communications']
    worklogs = []
    
    for inc in incidents:
        inc_id = inc[26] # Incident_ID
        inc_submit = datetime.strptime(inc[1], '%Y-%m-%d %H:%M:%S')
        
        # Generate 1 to 4 worklogs per incident
        for w in range(random.randint(1, 4)):
            wl_id = f"WL{str(uuid.uuid4())[:8]}"
            wl_date = inc_submit + timedelta(hours=random.randint(1, 24))
            submitter = random.choice(login_ids[:15])
            
            worklogs.append((
                wl_id, wl_date.strftime('%Y-%m-%d %H:%M:%S'), submitter, wl_date.strftime('%Y-%m-%d %H:%M:%S'),
                f"Update {w+1} for {inc_id}", f"Checked system logs. Found error code {random.randint(100, 999)}.",
                wl_date.strftime('%Y-%m-%d %H:%M:%S'), submitter, inc_id,
                random.choice(worklog_types), 'Web', 'Internal', 'No', wl_date.strftime('%Y-%m-%d %H:%M:%S')
            ))
    c.executemany('INSERT INTO hpd_worklog VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)', worklogs)

    conn.commit()
    conn.close()
    
    # Automatically seed an admin user
    try:
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        conn = sqlite3.connect('remedy_mock.db')
        c = conn.cursor()
        admin_id = str(uuid.uuid4())
        hashed_pw = pwd_context.hash("admin")
        c.execute("INSERT INTO users (id, username, password_hash, created_at) VALUES (?, ?, ?, ?)", 
                  (admin_id, "admin", hashed_pw, datetime.now().isoformat()))
        conn.commit()
        conn.close()
        print(f"✅ Auto-seeded 'admin' user (password: admin)")
    except Exception as e:
        print(f"⚠️ Could not auto-seed admin user: {e}")
        
    print(f"✅ Generated comprehensive BMC Remedy mock database with 5 tables.")

    print(f"   - Users: {len(people)}")
    print(f"   - Support Groups: {len(support_assocs)}")
    print(f"   - Incidents: {len(incidents)}")
    print(f"   - Worklogs: {len(worklogs)}")

if __name__ == "__main__":
    create_db()

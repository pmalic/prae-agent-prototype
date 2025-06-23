# Employee Database

This SQLite database contains employee information for a company with the following structure:

## Tables

### employee
**Primary table containing employee personal information**
- `emp_no` (INTEGER, PRIMARY KEY): Unique employee number
- `birth_date` (DATE): Date of birth
- `first_name` (TEXT): Employee's first name
- `last_name` (TEXT): Employee's last name
- `gender` (TEXT): Gender ('M' or 'F')
- `hire_date` (DATE): Date employee was hired

### department
**Department information**
- `dept_no` (TEXT, PRIMARY KEY): Department code (e.g., 'd001', 'd002')
- `dept_name` (TEXT, UNIQUE): Department name
- **Departments**: Customer Service, Development, Finance, Human Resources, Marketing, Production, Quality Management, Research, Sales

### dept_emp
**Employee-department assignments (many-to-many relationship)**
- `emp_no` (INTEGER, FOREIGN KEY): References employee.emp_no
- `dept_no` (TEXT, FOREIGN KEY): References department.dept_no
- `from_date` (DATE): Start date of department assignment
- `to_date` (DATE): End date of department assignment

### dept_manager
**Department manager assignments**
- `emp_no` (INTEGER, FOREIGN KEY): References employee.emp_no
- `dept_no` (TEXT, FOREIGN KEY): References department.dept_no
- `from_date` (DATE): Start date as manager
- `to_date` (DATE): End date as manager

### title
**Employee job titles over time**
- `emp_no` (INTEGER, FOREIGN KEY): References employee.emp_no
- `title` (TEXT): Job title
- `from_date` (DATE): Start date for this title
- `to_date` (DATE): End date for this title (NULL if current)
- **Titles**: Assistant Engineer, Engineer, Senior Engineer, Senior Staff, Staff, Technique Leader

### salary
**Employee salary history**
- `emp_no` (INTEGER, FOREIGN KEY): References employee.emp_no
- `amount` (INTEGER): Salary amount
- `from_date` (DATE): Start date for this salary
- `to_date` (DATE): End date for this salary

## Views

### current_dept_emp
**Current department assignments for employees**
- Shows the most recent department assignment for each employee
- Joins dept_emp with dept_emp_latest_date view

### dept_emp_latest_date
**Helper view to find latest department assignment dates**
- Groups dept_emp by emp_no to find MAX(from_date) and MAX(to_date)

## Common Query Patterns

When generating SQL queries for this database, consider these patterns:

1. **Employee Information**: Join employee with other tables using emp_no
2. **Current Status**: Use views or filter by to_date to get current assignments
3. **Historical Data**: Most tables have from_date/to_date for time-based queries
4. **Department Hierarchies**: Use dept_manager for management relationships
5. **Salary Analysis**: salary table has comprehensive salary history

## Date Handling

- All dates are stored in DATE format
- Use date comparisons for filtering by time periods
- to_date of '9999-01-01' typically indicates current/active records
- from_date and to_date create valid time ranges for most tables

## Example Queries

```sql
-- Get current employees with their departments
SELECT e.first_name, e.last_name, d.dept_name
FROM employee e
JOIN current_dept_emp de ON e.emp_no = de.emp_no
JOIN department d ON de.dept_no = d.dept_no;

-- Get current salary for an employee
SELECT e.first_name, e.last_name, s.amount
FROM employee e
JOIN salary s ON e.emp_no = s.emp_no
WHERE s.to_date = '9999-01-01';

-- Find department managers
SELECT e.first_name, e.last_name, d.dept_name
FROM employee e
JOIN dept_manager dm ON e.emp_no = dm.emp_no
JOIN department d ON dm.dept_no = d.dept_no
WHERE dm.to_date = '9999-01-01';
```
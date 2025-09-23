# SPARQL Cron Job Setup

This directory contains a cron job setup to automatically execute the SPARQL query `data/queries/location/populate.sparql` against the VeNiss SPARQL endpoint every hour.

## Files Created

- `run_sparql_query.sh` - Main execution script
- `.env.template` - Template for credentials (copy to `.env`)
- `SPARQL_CRON_SETUP.md` - This setup guide
- Updated `.gitignore` - Excludes credentials and logs from version control

## Setup Instructions

### 1. Create Credentials File

Copy the template and add your actual credentials:

```bash
cp .env.template .env
```

Edit `.env` and replace the placeholder values:
```bash
SPARQL_USERNAME=your_actual_username
SPARQL_PASSWORD=your_actual_password
```

### 2. Secure the Credentials File

Set restrictive permissions on the credentials file:

```bash
chmod 600 .env
```

### 3. Test the Script

Run the script manually to ensure it works:

```bash
./run_sparql_query.sh
```

Check the log file for results:
```bash
cat logs/sparql_cron.log
```

### 4. Set Up Cron Job

Add the cron job to run every hour:

```bash
crontab -e
```

Add this line to run at the beginning of every hour:
```bash
0 * * * * /Users/gspinaci/projects/veniss/apps/VeNiss/run_sparql_query.sh >/dev/null 2>&1
```

### 5. Verify Cron Job

Check that the cron job was added:
```bash
crontab -l
```

## Monitoring

- **Logs**: Check `logs/sparql_cron.log` for execution history
- **Cron Status**: Use `crontab -l` to verify the job is scheduled
- **Manual Testing**: Run `./run_sparql_query.sh` to test manually

## Troubleshooting

1. **Permission Denied**: Ensure the script is executable (`chmod +x run_sparql_query.sh`)
2. **Credentials Error**: Verify `.env` file exists and contains correct credentials
3. **Network Issues**: Check if the SPARQL endpoint is accessible
4. **Query Errors**: Verify the SPARQL query syntax in `data/queries/location/populate.sparql`

## Security Notes

- The `.env` file is excluded from version control
- Credentials are stored with restricted file permissions (600)
- All operations are logged with timestamps
- The cron job redirects output to prevent email spam

## SPARQL Query Details

The query (`data/queries/location/populate.sparql`) performs an INSERT operation that:
- Adds path information to archival collections
- Uses CIDOC-CRM ontology
- Builds hierarchical paths for collections
- Only processes items that don't already have paths
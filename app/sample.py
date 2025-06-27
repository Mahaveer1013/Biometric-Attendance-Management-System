import re

def check_date_format(date):
    # Regular expression patterns to match different date formats
    date_patterns = [
        r'(\d{2})[-./](\d{2})[-./](\d{4})',  # Matches formats like 09-12-2005, 09/12/2005, 09.12.2005
        r'(\d{4})-(\d{2})-(\d{2})',           # Matches format like 2005-12-09
        # Add more patterns if needed
    ]

    for pattern in date_patterns:
        match = re.match(pattern, date)
        if match:
            time_part = date.split()[1] if len(date.split()) > 1 else "00:00:00"
            # Extract components of the date
            if len(match.groups()) == 3:
                day, month, year = match.groups()
                formatted_date = f"{day}-{month}-{year} {time_part}"

            elif len(match.groups()) == 4:
                year, month, day = match.groups()
                formatted_date = f"{day}-{month}-{year} {time_part}"

            # Extract the time if available
            # Format the date in the desired format (DD-MM-YYYY hr:min:sec)
            return formatted_date

    # If none of the patterns match, return None
    return None

# Test the function
date = "2005-12-09 12:34:56"  # Example date with time
formatted_date = check_date_format(date)
if formatted_date:
    print("Formatted Date:", formatted_date)
else:
    print("Invalid date format")

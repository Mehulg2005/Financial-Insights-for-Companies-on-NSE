import pandas as pd


# --------------------------------------------------
# Convert scraped table into database format
# --------------------------------------------------

def process_scraped_data(
    data,
    nse_code,
    company_name
):

    if not data:
        return []


    # --------------------------------------------------
    # Find header row
    # --------------------------------------------------

    header_index = None

    for i, row in enumerate(data):

        if (
            "Mar 2016" in row
            or "Mar 2017" in row
            or "Mar 2026" in row
        ):

            header_index = i
            break


    if header_index is None:

        raise ValueError(
            "Could not find the period header row."
        )


    # --------------------------------------------------
    # Get column names
    # --------------------------------------------------

    columns = data[header_index]

    processed_columns = []

    for column in columns:

        column = column.strip()

        if column == "":
            processed_columns.append("Metric")

        else:
            processed_columns.append(column)


    if "Metric" not in processed_columns:

        raise ValueError(
            "Could not identify Metric column."
        )


    # --------------------------------------------------
    # Get table data
    # --------------------------------------------------

    table_data = data[
        header_index + 1:
    ]


    scraped_df = pd.DataFrame(
        table_data,
        columns=processed_columns
    )


    # --------------------------------------------------
    # Remove unit from Metric
    #
    # Example:
    #
    # Reliance Retail Store Count
    # Number
    #
    # becomes:
    #
    # Reliance Retail Store Count
    # --------------------------------------------------

    def clean_metric(metric):

        metric = str(metric)

        if "\n" in metric:

            metric = metric.split(
                "\n"
            )[0]

        return metric.strip()


    scraped_df["Metric"] = (
        scraped_df["Metric"]
        .apply(clean_metric)
    )


    # --------------------------------------------------
    # Convert wide format into long format
    # --------------------------------------------------

    records = []


    for _, row in scraped_df.iterrows():

        metric = row["Metric"]

        for column in scraped_df.columns:

            if column == "Metric":
                continue

            period = column

            value = row[column]


            # Ignore completely empty values

            if pd.isna(value):

                value = None

            elif str(value).strip() == "":

                value = None

            else:

                value = str(value).strip()


            records.append(
                {
                    "NSE_Code": nse_code,
                    "Company_Name": company_name,
                    "Metric": metric,
                    "Period": period,
                    "Value": value
                }
            )


    return records
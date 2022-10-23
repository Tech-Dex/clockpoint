import asyncio
import io

import pandas as pd

from app.schemas.v1.response import SessionsSmartReportResponse


async def build_in_memory_file(data: SessionsSmartReportResponse) -> bytes:
    output = io.BytesIO()
    result_futures = await asyncio.gather(
        _build_full_data(data),
        _build_attendance_list(data),
    )
    result_full_data, result_attendance_list = result_futures

    with pd.ExcelWriter(
        output,
        engine="xlsxwriter",
        datetime_format="dd-mm-yyyy hh:mm:ss",
    ) as writer:

        result_full_data.to_excel(writer, sheet_name=f"Sessions Full Data", index=False)
        result_attendance_list.to_excel(
            writer, sheet_name=f"Attendance List", index=False
        )

    return output.getvalue()


async def _build_full_data(
    data: SessionsSmartReportResponse,
) -> pd.DataFrame:
    df: pd.DataFrame = pd.DataFrame(
        columns=[
            "Session ID",
            "Session Start At",
            "Session Stop At",
            "Username",
            "Email",
            "First Name",
            "Last Name",
            "Clock In",
            "Clock Out",
        ],
    )

    for session in data.sessions:
        for entry in session.smart_entries:
            df = pd.concat(
                [
                    df,
                    pd.DataFrame(
                        [
                            [
                                session.details.clock_sessions_id,
                                session.details.start_at,
                                session.details.stop_at,
                                entry.username,
                                entry.email,
                                entry.first_name,
                                entry.last_name,
                                entry.clock_in,
                                entry.clock_out,
                            ]
                        ],
                        columns=[
                            "Session ID",
                            "Session Start At",
                            "Session Stop At",
                            "Username",
                            "Email",
                            "First Name",
                            "Last Name",
                            "Clock In",
                            "Clock Out",
                        ],
                    ),
                ],
                ignore_index=True,
            )
    return df


async def _build_attendance_list(
    data: SessionsSmartReportResponse,
) -> pd.DataFrame:
    df: pd.DataFrame = pd.DataFrame(
        columns=[
            "Username",
            "Email",
            "First Name",
            "Last Name",
        ],
    )

    for session in data.sessions:
        df[f"Session {session.details.start_at} - {session.details.stop_at}"] = "A"
        for entry in session.smart_entries:
            if df[df["Username"] == entry.username].empty:
                df = pd.concat(
                    [
                        df,
                        pd.DataFrame(
                            [
                                [
                                    entry.username,
                                    entry.email,
                                    entry.first_name,
                                    entry.last_name,
                                ]
                            ],
                            columns=[
                                "Username",
                                "Email",
                                "First Name",
                                "Last Name",
                            ],
                        ),
                    ],
                    ignore_index=True,
                )

            df.loc[
                df["Username"] == entry.username,
                f"Session {session.details.start_at} - {session.details.stop_at}",
            ] = "P"

    df["Present"] = ""
    df["Absent"] = ""
    for row in df.iterrows():
        df.loc[row[0], "Present"] = row[1].str.contains("P").sum()
        df.loc[row[0], "Absent"] = row[1].str.contains("A").sum()
    return df

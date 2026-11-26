from sqlalchemy import inspect, text


def ensure_schema(engine):
    """Add columns introduced after the initial snapshot on long-lived volumes.

    New databases are created directly from the SQLAlchemy metadata. This only
    patches pre-existing development MySQL/SQLite files where create_all does
    not ALTER tables.
    """
    inspector = inspect(engine)
    if 'folio_checks' not in inspector.get_table_names():
        return

    columns = {column['name'] for column in inspector.get_columns('folio_checks')}
    statements = []
    if 'status' not in columns:
        statements.append(
            "ALTER TABLE folio_checks ADD COLUMN status VARCHAR(16) "
            "NOT NULL DEFAULT 'checked'"
        )
    if 'state' not in columns:
        statements.append(
            "ALTER TABLE folio_checks ADD COLUMN state VARCHAR(32) "
            "NOT NULL DEFAULT '已核对'"
        )

    if statements:
        with engine.begin() as conn:
            for statement in statements:
                conn.execute(text(statement))

    if engine.dialect.name != 'mysql' or 'rescan_slots' not in inspector.get_table_names():
        return

    # The initial snapshot made check_ref unique. Spot-check rechecks may add
    # a missed bad page after an initial delivery, so supplemental slots need
    # a non-unique check_ref index.
    indexes = inspector.get_indexes('rescan_slots')
    with engine.begin() as conn:
        for index in indexes:
            if index.get('unique') and index.get('column_names') == ['check_ref']:
                conn.execute(text(
                    f"ALTER TABLE rescan_slots DROP INDEX `{index['name']}`"
                ))
        existing = {index['name'] for index in inspector.get_indexes('rescan_slots')}
        if 'ix_rescan_slots_check_ref' not in existing:
            conn.execute(text(
                'CREATE INDEX ix_rescan_slots_check_ref ON rescan_slots (check_ref)'
            ))

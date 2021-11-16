from functions_pkg.db_functions import MySQLConnection


def delete_equipment(mi_id: int) -> bool:
    """
    Удаление данного оборудования из всех таблиц
    :param mi_id:
    :return:
    """
    sql_delete_1 = f"DELETE FROM mis WHERE mi_id = {mi_id}"
    sql_delete_2 = f"DELETE FROM mis_departments WHERE MD_mi_id = {mi_id}"
    sql_delete_3 = f"DELETE FROM mis_vri_info WHERE vri_mi_id = {mi_id}"
    return MySQLConnection.execute_transaction_query(sql_delete_1, sql_delete_2, sql_delete_3)


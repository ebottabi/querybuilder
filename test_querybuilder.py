import unittest
import sqlite3
from querybuilder import Query

RESET_SCRIPT = '''\
drop table if exists my_table;
create table my_table(
    id integer primary key autoincrement,
    name text not null,
    age integer
);
insert into my_table (name, age) values ('mike', 19);
insert into my_table (name, age) values ('lisa', 22);
insert into my_table (name, age) values ('rebecca', 32);
'''

def rand_string(n=32):
    import md5

    with open('/dev/random') as f:
        return md5.md5(f.read(n)).hexdigest()

class QueryTests(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        unittest.TestCase.__init__(self, *args, **kwargs)
        self.conn = sqlite3.connect(rand_string() + '.db')
        
    def setUp(self):
        self.conn.executescript(RESET_SCRIPT)

    def testSelect(self):
        args = Query('my_table').select().sql()
        cur = self.conn.execute(*args)
        records = cur.fetchall()
        self.assertEqual(len(records), 3)

        args = Query('my_table').select('name').sql()
        cur = self.conn.execute(*args)
        record = cur.fetchone()
        self.assertEqual(len(record), 1)

        args = Query('my_table').select('name').where(age=22).sql()
        cur = self.conn.execute(*args)
        record = cur.fetchone()
        self.assertEqual(record[0], 'lisa')

    def testInsert(self):
        args = Query('my_table').insert(3).sql(values=[4, 'joe', 44])
        cur = self.conn.execute(*args)
        self.conn.commit()

        self.assertEqual(cur.lastrowid, 4)

        args = Query('my_table').insert({'name': 'beth', 'age': 21}).sql()
        cur = self.conn.execute(*args)
        self.conn.commit()
        cur = self.conn.execute('SELECT * FROM my_table WHERE id=?', [cur.lastrowid])
        record = cur.fetchone()
        self.assertIsNotNone(record)
        self.assertEqual(record[1], 'beth')

    def testUpdate(self):
        pass

    def testDelete(self):
        pass


if __name__ == '__main__':
    unittest.main()

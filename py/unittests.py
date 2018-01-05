#!/usr/bin/env python

import unittest
import model


class CursorTest(unittest.TestCase):

    def setUp(self):
        self.cursors = model.CursorList()

    def testAppend(self):
        n = 0
        for y in range(2):
            for x in range(2):
                self.cursors.append((x,y))
                n += 1
        self.assertEqual(len(self.cursors), n)

    def testDoubleAppend(self):
        cursor = (0,0)
        self.cursors.append(cursor)
        self.cursors.append(cursor)
        self.assertEqual(len(self.cursors), 2)

    def testRemove(self):
        cursor = (0,0)
        self.cursors.append(cursor)
        self.cursors.remove(cursor)
        self.assertEqual(len(self.cursors), 0)

    def tearDown(self):
        self.assertEqual(len(self.cursors), len(self.cursors._orderLeftToRight))
        self.assertEqual(len(self.cursors), len(self.cursors._orderTopToBottom))
        
        self.assertEqual(sorted(self.cursors._orderLeftToRight), range(len(self.cursors)))
        self.assertEqual(sorted(self.cursors._orderTopToBottom), range(len(self.cursors)))
    


if __name__=='__main__':
    unittest.main()
    pass

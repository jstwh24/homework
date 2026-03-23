class HashTable:
    def __init__(self, size=10):
        self.size = size
        self.table = [[] for _ in range(self.size)]

    def _hash_function(self, key):
        """取键的哈希值对数组长度取模"""
        return hash(key) % self.size

    def insert(self, key, value):
        """插入或更新键值对"""
        index = self._hash_function(key)
        for i, (k, v) in enumerate(self.table[index]):
            if k == key:
                self.table[index][i] = (key, value)
                return
        self.table[index].append((key, value))

    def get(self, key):
        """根据键获取值"""
        index = self._hash_function(key)
        for k, v in self.table[index]:
            if k == key:
                return v
        return None  

    def delete(self, key):
        index = self._hash_function(key)
        for i, (k, v) in enumerate(self.table[index]):
            if k == key:
                del self.table[index][i]
                return True
        return False


ht = HashTable(5)
ht.insert("apple", 10)
ht.insert("banana", 20)
ht.insert("cherry", 30)
ht.delete("banana")

print(f"apple 的值: {ht.get('apple')}")   # 输出 10
print(f"banana 的值: {ht.get('banana')}")   # 输出 None
print(f"cherry 的值: {ht.get('cherry')}")   # 输出 30
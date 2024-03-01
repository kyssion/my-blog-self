有几个东西新学的. 

1. 伪共享 . 就是说内存获取数据的时候是一次性的拿取一个空间的数据进行计算. 如果能把一次迭代的数据都放在cpu一次读取的空间中的话, 性能就会大大的提升 . 比如下面的java代码

```java
class CacheLineEffect {
    //考虑一般缓存行大小是64字节，一个 long 类型占8字节
    static  long[][] arr;

    public static void main(String[] args) {
        arr = new long[1024 * 1024][];
        for (int i = 0; i < 1024 * 1024; i++) {
            arr[i] = new long[8];
            for (int j = 0; j < 8; j++) {
                arr[i][j] = 0L;
            }
        }
        long sum = 0L;
        long marked = System.currentTimeMillis();
        for (int i = 0; i < 8; i+=1) {
            for(int j =0; j< 1024 * 1024;j++){
                sum = arr[j][i];
            }
        }
        System.out.println("Loop times:" + (System.currentTimeMillis() - marked) + "ms");

        marked = System.currentTimeMillis();
        for (int i = 0; i < 1024 * 1024; i+=1) {
            for(int j =0; j< 8;j++){
                sum = arr[i][j];
            }
        }
        System.out.println("Loop times:" + (System.currentTimeMillis() - marked) + "ms");
    }
}

```

2. 第二个就是伪共享 . 还是针对上面cpu获取数据 , 如果变量A 和B 都在cpu这次取数的空间里 , 尽管代码用的只用了A , B 其实也会被标记使用, 会让java 重新同步数据保证数据可见性.

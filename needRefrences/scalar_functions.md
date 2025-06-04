预定义标量函数列表
函数名签名	函数功能
ABS(<x>)	计算x的绝对值
ACOS(<x>)	计算x的反余弦值
ARRAY_AT(<multi_value>, <index>)	获取数组multi_value[index]的值,注意:index从0开始
ARRAY_APPEND(<multi_value>, <element>)	向数组multi_value的尾部追加一个元素element
ARRAY_APPEND_AT(<multi_value>, <element>,<index>)	在数组的第index处插入一个元素，注意:index从0开始
ARRAY_CAT(<multi_value1>,<multi_value2>)	将两个数组合并为一个数组
ARRAY_CONTAINS(<multi_value>, <element>)	检查数组multi_value是否包含某个元素element
ARRAY_DISTINCT(<multi_value>)	返回一个新的数组，其中只包含输入数组中的不同元素。该函数将排除输入的数组中的任何重复元素
ARRAY_GENERATE_RANGE(<start>,<stop>,<step>)	start:返回的数字范围中的第一个数字;stop:范围内的最后一个数字。请注意，这个数字不包括在返回的数字范围内。step:数组中每个后续数字的递增或递减量。注意，该数字只能为整数
ARRAY_JOIN(<multi_value>,<delimiter>)	使用分隔符delimiter将数组multi_value连接起来，并返回一个字符串。注意，分隔符delimiter的类型为字符串
ARRAY_LENGTH(<multi_value>)	计算数组的元素个数
ARRAY_MAX(<multi_value>)	计算数组的最大值
ARRAY_MIN(<multi_value>)	计算数组的最小值
ARRAY_POSITION(<multi_value>, <element>)	返回数组multi_value中元素 element首次出现的索引。注意，索引从0开始
ARRAY_PREPEND(<multi_value>, <element>)	向数组multi_value的头部追加一个元素element
ARRAY_REGEX_LIKE(<multi_value>, <regex_expr>)	对数组multi_value的每个元素应用正则表达式regex_expr，符合正则表达式regex_expr的元素将被保留到作为结果输出的数组中。注意:该正则表达式应符合posix regex正则表达式标准
ARRAY_REMOVE_AT(<multi_value>, <index>)	在数组的第index处移除该元素，注意:index从0开始
ARRAY_SLICE(<multi_value>, <from>,<to>)	返回输入的数组multi_value的子数组。from:源数组中的某个索引。第一个元素的位置为 0，小于 from 位置的元素不包含在结果数组中。to:源数组中的某个索引。结果数组中不包含来自等于或大于 to 的位置的元素。
ARRAY_SORT(<multi_value>, <sort_ascending>)	返回一个数组，其中包含按升序或降序排序的输入multi_value的元素。sort_ascending指定 "true"，按升序对元素排序。sort_ascending指定 "false"，按降序对元素排序。
ARRAY_SPLIT(<string>,<separator>)	用给定的string类型的分隔符separator分割给定的字符串，并将结果以数组的形式返回。
ARRAY_INTERSECT(<multi_value1>,<multi_value2>)	返回两个数组的交集
ARRAY_EXCEPT(<multi_value1>,<multi_value2>)	返回一个新的数组，其中包含来自一个输入数组中multi_value1不存在于另一个输入数组multi_value2中的元素
ASCII(<x>)	返回x的ASCII编码值
ASIN(<x>)	计算x的反正弦值
ATAN(<x>)	计算x的反正切值
BAR(<x>,<min>,<max>,<width>)	建立条形图。select bar(x, min, max, width)绘制一个条形图，条形图与(x - min)成比例，并在x = max时条形图宽度等于width
BIT_LENGTH(<str>)	计算给定字符串的比特位数
BIN(<int>)	计算给定整数的二进制字符串
BITWISE_AND(<x>, <y>)	计算给定两个数值的按位与
BITWISE_NOT(<x>)	计算给定数值的按位取反
BITWISE_OR(<x>, <y>)	计算给定两个数值的按位或
BITWISE_XOR(<x>, <y>)	计算给定两个数值的按位异或
BROUND(<x>)	用HALF_EVEN规则对x进行取整运算
BTRIM(<str>)	去除字符串两端的空格
BTRIM(<str>, <chars>)	去除字符串两端的字符，如果这些字符在第二个参数给出的字符集合内
CBRT(<x>)	计算给定输入的立方根
CEIL(<x>)	计算x向上取整值
CHAR_LENGTH(<str>)	返回字符串的长度
CHARACTER_LENGTH(<str>)	同CHAR_LENGTH(<str>)
CHR(<num>)	返回参数num对应的ASCII字符
CIDR_MATCH(<ip_field>, <cidr_str>)	对ip_field字段使用cidr_str进行过滤
COALESCE(<opt_1>, <opt_2>, ...)	返回所给参数中第一个非空的值，可用作填充空值空能
CONCAT(<str1>, <str2>, ...)	把字符串str1, str2, ... 串联在一起，最多可连接10个字符串
CONCAT_WS(<con>, <str1>, <str2>, ...)	把字符串str1, str2, ... 用连接符con串联在一起，最多可连接5个字符串
CONTAINS(<str>)	检查原始数据中是否存在关键字str；str必须是字符串类型的字面量，且大小写不敏感
CONV(<num>,<from_radix>,<to_radix>)	把原始进制from_radix对应的字符串数值num按期望进制to_radix转化为相应字符串，其中from_radix与to_radix都为整数，并且它们的范围都在[2,36]
COS(<x>)	计算x的余弦值
COSH(<x>)	计算x的双曲余弦函数值
COT(<x>)	计算x的余切值
CRC32(<str>)	计算str的CRC32值
CUT_QUERY_STRING(<url>)	删除URL中的查询字符串。例如:select cut_query_string('https://www.example.com:8080/foo/bar?baz=qux')，返回 https://www.example.com:8080/foo/bar
CUT_QUERY_STRING_AND_FRAGMENT(<url>)	删除URL中的查询字符串和片段标识符。例如:select cut_query_string_and_fragment('https://www.example.com:8080/foo/bar?baz=qux#quux')，返回 https://www.example.com:8080/foo/bar
CUT_WWW(<url>)	删除 URL 域名开头的 "www"
DAMERAU_LEVENSHTEIN_DISTANCE(<str>,<str>)	计算两个字符串之间的Damerau-Levenshtein距离
DATE_ADD(<time_unit>, <delta>)	基于当前的系统时间，增加时间的偏移量；<time_unit>只能是常量字符串s,m,h,d等，可参考时间字面量；delta是一个整数类型的表达式，表示要改变的时间偏移量
DATE_ADD(<time_unit>, <delta>, <base_timestamp>)	在给定出的<base_timestamp>的基础上，增加时间的偏移量；<time_unit>只能是常量字符串s,m,h,d等，可参考时间字面量；delta是一个整数类型的表达式，表示要改变的时间偏移量；base_timestamp是时间戳类型的表达式，可参考时间字面量
DATE_DIFF(<time_unit>, <start_timestamp>, <end_timestamp>)	计算给定时间单位上两个时间戳的差值 end_timestamp - start_timestamp；<time_unit>只能是常量字符串s,m,h,d等，可参考时间字面量；例如 DATE_DIFF('year', '2021-02-02T00:00:00', '2022-03-02T00:00:00')得到结果1
DATE_PART(<time_unit>, <timestamp>)	计算给定时间单位上时间戳对应的值；<time_unit>可以是常量字符串s,m,h,d等，可参考时间字面量，此外还可以是millennium,century,decade,doy(day of year),dow(day of week),dom(day of month),woy(week of year)；例如 DATE_PART('year', '2021-02-02T00:00:00')得到结果2021
DATE_TRUNC(<time_unit>, <timestamp>)	计算精确到给定时间单位上时间戳的值；<time_unit>只能是常量字符串s,m,h,d等，可参考时间字面量；例如 DATE_TRUNC('year', '2021-02-02T00:00:00')得到结果2021-01-01T00:00:00
DEGREES(<x>)	计算弧度x对应的角度值
DOMAIN(<url>)	从字符串url中提取域名
DOMAIN_WITHOUT_WWW(<url>)	返回域名，并删除域名开头不超过一个的 "www."（如果存在）
ELT(<idx>, <str1>, <str2>, ...)	返回给定字符串str1,str2 ...(最多可有5个选项)中第idx个选项
ENDS_WITH(<str>, <sub_str>)	检测字符串str是否以sub_str结尾，返回boolean；如果返回true，就表示第一个参数的值的结尾是sub_str；如果是false，则表示不是以sub_str结尾
EXP(<x>)	计算 $e^x$，x 表示参数，e 是欧拉常数(Euler's Constant)，自然对数的底数
FACTORIAL(<x>)	计算x的阶乘
FLOOR(<x>)	计算x向下取整值
FORMAT(<format_str>,<str_1>,<str_2>, ...)	向给定字符串format_str按给定位置进行字符串填充。字符串的填充位置从1开始计数。最多可以填充5个字符串。例如format('hello_{1}','world'),其结果为字符串'hello_world'
FRAGMENT(<utf>)	返回片段标识符。片段不包括初始哈希符号。例如:select fragment('https://www.example.com:8080/foo/bar?baz=qux#quux');，返回 quux
GREATEST(<opt_1>, <opt_2>, ...)	返回所给参数中的最大值
HAMMING_DISTANCE(<str>,<str>)	计算两个字符串之间的HAMMING距离
HASH(<input>)	计算给出的字段的32位整数哈希值，参数可以是一个常量
HASH32(<input>)	同HASH(<input>)
HASH64(<input>)	计算给出的字段的64位整数哈希值，参数可以是一个常量
HASH_MD5(<input>)	计算给出的字段的MD5加密哈希值，参数可以是一个常量
HASH_SHA1(<input>)	计算给出的字段的SHA1加密哈希值，参数可以是一个常量
HASH_SHA256(<input>)	计算给出的字段的SHA256加密哈希值，参数可以是一个常量
HEX(<input>)	计算input的16进制的值
ILIKE(<source>, <pattern>)	返回source是否符合pattern的格式；pattern中_表示任意字符，%表示任意字符串，大小写不敏感
INITCAP(<input>)	返回将input转成单词首字母大写的字符串；例如 INITCAP('server FAILED On tUesDAy')返回'Server Failed On Tuesday'
INT_TO_IP(<input>)	计算给出的整数对应的ip地址；例如 INT_TO_IP(3232287244)返回'192.168.202.12'
INT_TO_IP(<input>, <is_from_low_to_high>)	计算给出的整数对应的ip地址，如果is_from_low_to_high是TRUE将按照从低位到高位处理给定的整数；例如INT_TO_IP(3232287244, TRUE)返回'12.202.168.192'，INT_TO_IP(3232287244, FALSE)返回'192.168.202.12'
IP_TO_INT(<input>)	计算给出的ip地址字符串对应的整数值；例如 IP_TO_INT('192.168.202.12')返回3232287244
IP_TO_INT(<input>, <is_from_low_to_high>)	计算给出的ip地址字符串对应的整数值，如果is_from_low_to_high是TRUE将按照从低位到高位处理返回的整数；例如IP_TO_INT('192.168.202.12', TRUE)返回214608064，IP_TO_INT('192.168.202.12', FALSE)返回3232287244
IPV4_TO_IPV6(<ipv4>)	计算给定的ipv4字符串为ipv6字符串
IS_ASCII(<str>)	判断给定的字符串是否是ascii编码
IS_IPV4(<str>)	判断给定的字符串ip地址是否属于ipv4地址
IS_IPV4_LOOPBACK(<str>)	判断给定的字符串ipv4地址是否属于ipv4回环地址
IS_IPV6(<str>)	判断给定的字符串ip地址是否属于ipv6地址
IS_IPV6_LOOPBACK(<str>)	判断给定的字符串ipv6地址是否属于ipv6回环地址
IS_SUBSTR(<str>, <str_sub>)	检测字符串str是否包含sub_str，返回boolean；如果返回true，则表示包含，否则是不包含
IS_VALID_URL(<url>)	判断1个url是否是有效的
JARO_SIMILARITY(<str>,<str>)	根据Jaro Similarity定义，计算两个字符串之间的相似性
JARO_WINKLER_SIMILARITY(<str>,<str>)	根据Jaro–Winkler similarity定义，计算两个字符串之间的相似性
JSON_POINTER(str1, str2)	解析json字符串str1，并用str2所表达的json pointer路径返回json文档的值，结果为字符串类型
JSON_POINTER_MV(str1, str2)	解析json字符串str1，并用str2所表达的json pointer路径返回json文档的值，结果为字符串的多值类型
LEFT(<source>, <chars_num>)	返回source左边chars_num个字符串
LEAST(<opt_1>, <opt_2>, ...)	返回所给参数中的最小值
LENGTH(<str>)	同CHAR_LENGTH(<str>)
LEVENSHTEIN(<str1>, <str2>)	计算str1和str2的LEVENSHTEIN距离
LOCATE(<sub_str>, <str>)	查找sub_str在str中第一次出现的位置；注意，位置是从1开始的；例如LOCATE('he', 'hello')返回1；如果sub_str在str没有出现，返回0
LOCATE(<sub_str>, <str>, <start_position>)	从sub_str的第start_position个字符开始查找，查找sub_str在str中第一次出现的位置；例如LOCATE('ll', 'hello', 2)返回3，LOCATE('ll', 'hello', 4)返回0
LOG(<x>)	计算一个数的自然对数, $ln(x)$，x 表示参数，对数的底数是欧拉常数(Euler's Constant)
LOG(<base>, <x>)	计算一个数的对数, 第一个参数是对数的底数
LOG10(<x>)	计算一个数的10位底数的对数, $LOG(x)$，x表示参数，对数的底数是10
LOWER(<str>)	将输入的字符串转换成小写
LPAD(<source>, <chars_num>, <padstr>)	将source左侧填充字符串padstr，直到总字符串长度达到chars_num后返回结果
LPAD(<source>, <chars_num>)	等价于LPAD(<source>, <chars_num>, ' ')
LTRIM(<str>)	去除输入字符串开头的空格
LTRIM(<str>, <chars>)	去除输入字符串开头的字符，如果这些字符在第二个参数给出的字符集合内
MASK_FIRST_N(<str>, <a>)	将str中的前a个字符用字符 x 或 n 代替
MASK_LAST_N(<str>, <a>)	将str中的后a个字符用字符 x 或 n 代替
MOD(<x>, <y>)	计算x对y取模的值
NETLOC	从 URL 中提取网络位置信息。例如:select netloc('https://me:my_pass@www.example.com:8080/foo/bar?baz=qux#quux')，返回 me:my_pass@www.example.com:8080
NETLOC_USERNAME(<url>)	从url中提取用户信息。例如:select netloc_username('https://me:my_pass@www.example.com:8080/foo/bar?baz=qux#quux'),返回 me
NETLOC_PASSWORD(<url>)	从url中提取用户信息。例如:select netloc_password('https://me:my_pass@www.example.com:8080/foo/bar?baz=qux#quux'),返回 mypass
NORMALIZED_DAMERAU_LEVENSHTEIN_DISTANCE(<str>,<str>)	计算两个字符串根据Damerau–Levenshtein算法在 0.0 和 1.0之间的归一化得分，其中 1.0 表示字符串相同
NORMALIZED_LEVENSHTEIN_DISTANCE(<str>,<str>)	计算两个字符串根据Levenshtein算法在 0.0 和 1.0之间的归一化得分，其中 1.0 表示字符串相同
NOW()	返回系统当前时间
NULLIF(<x>, <y>)	如果x等于y，返回空值，否则返回x的值
OCTET_LENGTH(<str>)	返回字符串所占字节的长度
OSA_DISTANCE(<str>,<str>)	根据OSA算法计算两个字符串之间的距离
PATH(<utr>)	返回路径。例如:select path('https://www.example.com:8080/foo/bar'),这将返回 foo/bar
PATH_FULL(<utr>)	与path函数功能一致，但是返回相应字符串和片段。例如:select path_full('https://www.example.com:8080/foo/bar?baz=qux'),返回 /foo/bar?baz=qux
PMOD(<x>, <y>)	返回x对y的正取余值
PORT(<utr>)	返回端口，如果 URL 中没有端口（或出现验证错误），则返回对应URL协议的默认端口
POSITION(<sub_str>, <str>)	同LOCATE(<sub_str>, <str>)
POSITION(<sub_str>, <str>, <start_position>)	同LOCATE(<sub_str>, <str>, <start_position>)
POW(<x>, <y>)	幂次方运算, 相当于计算 $x^y$ 第一个参数是幂次方的底数
POWER(<x>, <y>)	同POW(<x>, <y>)
PROTOCOL(<url>)	从 字符串url中提取对应协议，例如http,https等
QUERY_STRING(<utr>)	返回查询字符串。例如:select query_string('https://www.example.com:8080/foo/bar?baz=qux')，返回 baz=qux
QUOTE(<str>)	返回str被单引号引用的结果
RADIANS(<x>)	计算角度x对应的弧度值
RAND()	生成一个[0, 1)之间的随机数；范围包括0，但是不包括1；在同一投影(Projection)中同时调用多次的结果并不相同
RAND(<int>)	生成一个[0, 1)之间的随机数；范围包括0，但是不包括1；在同一投影(Projection)中同时调用多次，且传入的int值相同，则结果相同；int必须是字面量整数
RANDOM()	同RAND()
RANDOM(<int>)	同RAND(<int>)
REGEXP_REPLACE(<str>, <regex>, <rep>)	将str中匹配正则表达式regex的部分用rep替换
REGEX_LIKE(<source>,<regex>,<parameter>)	返回source是否符合regex表达式。总计有4个参数可以组合选择:(i,c,n,m)。其中'i' 表示不区分大小写的匹配。'c' 表示区分大小写的匹配。'n' 允许点（.），即匹配任何字符的通配符字符，匹配换行符。如果省略此参数，则点不匹配换行符。'm' 将源字符串视为多行。炎凰数据平台将 ^ 和 $ 解释为源字符串中的任何位置的行的开头和结尾，而不仅仅是整个源字符串的开头或结尾。如果省略此参数，则将源字符串视为单行。例如REGEXP_LIKE (last_name, '([aeiou])\1', 'inm');
REMOVE_CHARS(<str>, <chars_to_remove>)	将chars_to_remove中的每个字符从str中移除；例如，REMOVE_CHARS('$960,000.00', '$,')返回'960000.00'
REPEAT(<str>, <x>)	返回str重复x次的结果
REPLACE(<str>, <str1>, <str2>)	把str中所有出现的子串str1替换成str2
REVERSE(<str>)	将输入的字符串反转
RIGHT(<source>, <chars_num>)	返回source右边chars_num个字符串
ROUND(<x>)	计算x的约数，只取整数部分，小数部分四舍五入
ROUND(<x>, <y>)	计算x的约数，即四舍五入值，y为保留/舍弃的位数；当y大于零时，y表示保留小数点后的位数；当y小于零时，y的绝对值表示舍弃小数点前的位数；当y等于零或者缺省时，表示舍弃所有小数且仅保留整数部分
RPAD(<source>, <chars_num>, <padstr>)	将source右侧填充字符串padstr，直到总字符串长度达到chars_num后返回结果
RPAD(<source>, <chars_num>)	等价于RPAD(<source>, <chars_num>, ' ')
RTRIM(<str>)	去除字符串结尾的空格
RTRIM(<str>, <chars>)	去除字符串结尾的字符，如果这些字符在第二个参数给出的字符集合内
SIN(<x>)	计算x的正弦值
SINH(<x>)	计算x的双曲正弦函数值
SORENSEN_DICE_SIMILARITY(<str>,<str>)	计算两个字符串的Sørensen–Dice coefficient相似性距离
SOUNDEX(<str>)	返回str的SOUNDEX值
SPACE(<num>)	返回num个空白符' '
SPLIT_PART(<base_str>, <split_str>, <index>)	用split_str把SPLIT_PARTbase_str分割，返回第index个分割值；例如SPLIT_PART('hello', 'll', 1)返回'he'
STARTS_WITH(<str>, <sub_str>)	检测字串str是否以sub_str开头，返回boolean；如果返回true，就表示第一个参数的值的开头是sub_str；如果是false，则表示不是以sub_str开头
STRFTIME(<microsecond_since_epoch>, <format>)	把epoch以微秒为单位的时间戳microsecond_since_epoch根据给定的格式format转换成时间戳字符串，时区为偏好设置中的时区。format支持的格式可以参考这里。具体例子可以看这里
STRFTIME(<microsecond_since_epoch>, <format>, <timezone>)	把epoch以微秒为单位的时间戳microsecond_since_epoch根据给定的格式format和时区timezone转换成时间戳字符串；format支持的格式可以参考这里；timezone参考这个页面的 TZ database name。具体例子可以看这里；某些场景中，亦可实现日期分桶的效果，参考用例
STRPTIME(<timestamp_string>, <format>)	把时间戳字符串timestamp_string根据给定的格式format转换成以微秒为单位的时间戳，如给定的格式format中没有指定时区信息，将按照偏好设置中的时区处理；format支持的格式可以参考这里
STRPTIME(<timestamp_string>, <format>, <timezone>)	把时间戳字符串timestamp_string根据给定的格式format和时区timezone转换成以微秒为单位的时间戳，如format中有合法的时区信息，将忽略timezone的内容；format支持的格式可以参考这里；timezone参考这个页面的 TZ database name。具体例子可以看这里
SUBSTR(<str>, <start>)	返回第一个参数输入的字符串的一部分；start是一个整数，表示返回的子串在str的起始位置，如果start>0，则表示从头数的位数，需要注意的是位数从1开始；如果start<0， 则表示从字符串尾部开始向前数的位数；子串一直从起始位置到字符串结束； 例如：SUBSTR('hello', 1)返回hello，SUBSTR('hello', -2)返回lo
SUBSTR(<str>, <start>, <len>)	返回第一个参数输入的字符串的一部分；start是一个整数，表示返回的子串在str的起始位置，如果start>0，则表示从头数的位数，需要注意的是位数从1开始；如果start<0， 则表示从字符串尾部开始向前数的位数；len是子串的长度； 例如：SUBSTR('hello', 1, 2)返回he，SUBSTR('hello', -2, 3)返回lo
SUBSTRING(<str>, <start>)	同SUBSTR(<str>, <start>)
SUBSTRING(<str>, <start>, <len>)	同SUBSTR(<str>, <start>, <len>)
TAN(<x>)	计算x的正切值
TANH(<x>)	计算x的双曲正切函数值
TIME_BUCKET(<time_unit>, <field>)	把field字段按照time_unit进行时间聚合，支持的单位为秒s，分钟m，小时h，天d，周w，月M，季度q，年y。例如TIME_BUCKET('1d', _time)可以将_time字段的时间聚合到以1天为单位的时间上。时间单位之前必须是一个正整数
TIME_BUCKET(<time_unit>, <field>, <origin_timestamp>)	将桶的起始时间以origin_timestamp对齐，例如TIME_BUCKET('1d', _time,'2021-12-21T00:06:40.000+08:00')可以将_time字段的时间聚合到以1天为单位的时间上并以2021-12-21T00:06:40.000+08:00时间戳为分桶起点，假设_time为2021-08-07T09:12:13.000+08:00,则会输出2021-08-07T00:06:40.000+08:00
TOP_LEVEL_DOMAIN(<utr>)	从 URL 中提取顶级域。例如:SELECT top_level_domain('svn+ssh://www.some.svn-hosting.com:80/repo/trunk');输出为com
TRUNC(<x>)	计算x的舍位值，仅保留整数部分
TRUNC(<x>, <y>)	计算x的舍位值，y为保留/舍弃的位数；当y大于零时，y表示保留小数点后的位数；当y小于零时，y的绝对值表示舍弃小数点前的位数；当y等于零或者缺省时，表示舍弃所有小数且仅保留整数部分
TRUNCATE(<x>)	同TRUNC(<x>)
TRUNCATE(<x>, <y>)	同TRUNC(<x>, <y>)
UPPER(<str>)	将输入的字符串转换成大写
UNBASE64_STRING(<str>)	将输入的base64编码解码
URL_DECODE(<str>)	将输入的URL编码解码
UUID()	生成一个UUID
VALID_JSON(<str>)	输入1个json的字符串，判断该字符串表示的json是否合法
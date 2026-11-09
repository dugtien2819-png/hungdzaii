// Viết hàm hoán đổi giá trị của 2 biến
// Đầu vào của hàm: a = 3, b = 4
// Đầu ra của hàm: a = 4, b = 3
 
#include <iostream>
using namespace std;
 
void doi_2_so(int x, int y)
{
    int temp = x;
    x = y;
    y = temp;
}
 
int main()
{
    int a = 3;
    int b = 4;
    doi_2_so(a, b);
    cout << "a = " << a << endl;
    cout << "b = " << b << endl;
}
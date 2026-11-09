#include <iostream>
using namespace std;
int main() {
 int n, tich = 1;
 cout << "Nhap n: ";
 cin >> n;
 for (int i = 2; i <= n; i++)
 tich *= i;
 cout << "Tich = " << tich;
 return 0;
}
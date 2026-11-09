#include <iostream>
using namespace std;
int main() {
    int n;
    cout << "Nhap n: ";
    cin >> n;
    int dem = 0;

    while (n > 0)
    {
        // B1: Tách số 5 ra khỏi số 12345
        n = n / 10; // 1234
        dem++;      // dem = 1
    }
    cout << dem;
    return 0;
}
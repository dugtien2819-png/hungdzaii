#include <iostream>
using namespace std;

int main() {
    int tonggiay;
    int 
    cout << "Nhap tong so phut, diem 3 bai kiem tra: ";
    cin >> tongphut >> diem1 >> diem2 >> diem3;

    int sogio = tongphut / 60;
    int sophutle = tongphut % 60;

    double diemTB = (double)(diem1 + diem2 + diem3) / 3;
    
    int diemnguyen = (int)diemTB;
   
    int dat = (diemTB >= 5.0) && (sogio >= 1);

    cout << "Thoi gian hoc: " << sogio << " gio " << sophutle << " phut" << endl;
    
    
    cout << "Diem trung binh: " << diemTB << endl;
    cout << "Phan nguyen cua diem: " << diemnguyen << endl;
    cout << "Dat: " << dat << endl;

    return 0;
}
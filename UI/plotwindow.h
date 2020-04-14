#ifndef PLOTWINDOW_H
#define PLOTWINDOW_H

#include <QMainWindow>

namespace Ui {
class PlotWindow;
}

class PlotWindow : public QMainWindow
{
    Q_OBJECT

public:
    explicit PlotWindow(QWidget *parent = nullptr);
    ~PlotWindow();

private:
    Ui::PlotWindow *ui;
};

#endif // PLOTWINDOW_H

#include "plotwindow.h"
#include "ui_plotwindow.h"

PlotWindow::PlotWindow(QWidget *parent) :
    QMainWindow(parent),
    ui(new Ui::PlotWindow)
{
    ui->setupUi(this);
}

PlotWindow::~PlotWindow()
{
    delete ui;
}

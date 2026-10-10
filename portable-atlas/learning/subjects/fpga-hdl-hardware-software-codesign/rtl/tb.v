`timescale 1ns/1ps
module tb;
  reg clk=0, rst=0, en=0;
  wire [1:0] q,p,bq,bp,aq,ap;
  counter good(clk,rst,en,q,p);
  counter_bug bug(clk,rst,en,bq,bp);
  counter_async asyn(clk,rst,en,aq,ap);
  task tick;
    input [1:0] eq, ep;
    begin
      clk=1; #1; // after NBA commit, not active-region race
      if(q !== eq || p !== ep) $fatal(1,"oracle mismatch");
      $display("q=%d prev=%d bug=%d,%d async=%d,%d",q,p,bq,bp,aq,ap);
      clk=0; #1;
    end
  endtask
  initial begin
    $dumpfile("counter.vcd"); $dumpvars(0,tb);
    rst=1; tick(0,0); rst=0; en=1;
    tick(1,0); if(bp !== 1) $fatal(1,"bug not exposed");
    tick(2,1); tick(3,2); tick(0,3);
    en=0; tick(0,0); en=1; tick(1,0);
    rst=1; #1; if(aq !== 0 || q !== 1) $fatal(1,"pulse boundary");
    rst=0; #1; tick(2,1);
    rst=1; tick(0,0); $finish;
  end
endmodule

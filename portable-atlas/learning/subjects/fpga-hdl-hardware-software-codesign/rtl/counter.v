module counter(input wire clk, rst, en, output reg [1:0] q, prev);
  always @(posedge clk) begin
    if (rst) begin q <= 2'b00; prev <= 2'b00; end
    else begin
      if (en) q <= q + 2'b01;
      prev <= q; // RHS is pre-edge q, not q_next
    end
  end
endmodule
module counter_bug(input wire clk, rst, en, output reg [1:0] q, prev);
  wire [1:0] q_next = en ? q + 2'b01 : q;
  always @(posedge clk) begin
    if (rst) begin q <= 0; prev <= 0; end
    else begin q <= q_next; prev <= q_next; end // intentional lost delay
  end
endmodule
module counter_async(input wire clk, rst, en, output reg [1:0] q, prev);
  always @(posedge clk or posedge rst) begin
    if (rst) begin q <= 0; prev <= 0; end
    else begin if (en) q <= q + 2'b01; prev <= q; end
  end
endmodule
